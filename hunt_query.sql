-- Define an expanded list of Shadow AI domains/endpoints
WITH shadow_ai_indicators AS (
  SELECT * FROM UNNEST([
    -- LLM/Chat UIs & APIs
    'chat.openai.com', 'api.openai.com',
    'claude.ai', 'api.anthropic.com',
    'gemini.google.com', 'generativelanguage.googleapis.com',
    'perplexity.ai',
    'bard.google.com',
    -- Code Assistants
    'github.copilot.com', 'api.github.com',
    'cursor.sh', 'cursor.ai',
    -- Content/Copywriting
    'jasper.ai', 'api.jasper.ai',
    'copy.ai', 'api.copy.ai',
    -- Image Generation
    'midjourney.com',
    -- Model Hosting/Hubs
    'huggingface.co',
    -- Common API base URLs
    'models.googleapis.com',
    'ai.google.dev',
    'api.cohere.ai'
  ]) AS indicator
)

-- Query our proxy logs from the last 30 days
SELECT
  user_id,
  source_ip,
  requested_url, -- Matches schema from parse_logs.py output
  user_agent,
  COUNT(*) AS connection_count,
  -- bytes_sent is INTEGER in schema, IFNULL handles potential future NULLs
  SUM(IFNULL(bytes_sent, 0)) AS total_bytes_sent
FROM
  `shadow-ai-secops-project.security_logs.proxy_http_logs` -- Replace with your project/dataset/table if different
WHERE
  -- Attempt to parse the timestamp string and filter for the last 30 days
  -- Assumes format: 31/Dec/2017:23:07:28 +0000 -> %d/%b/%Y:%H:%M:%S %z
  SAFE.PARSE_TIMESTAMP('%d/%b/%Y:%H:%M:%S %z', timestamp) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  AND
  -- Check if the requested_url contains any of the indicators
  EXISTS (
    SELECT 1
    FROM shadow_ai_indicators
    WHERE STRPOS(requested_url, indicator) > 0
  )
GROUP BY
  user_id,
  source_ip,
  requested_url,
  user_agent
ORDER BY
  total_bytes_sent DESC
LIMIT 100;

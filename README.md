# Shadow AI Detection Project

## Overview

This project demonstrates a simulated Security Operations (SecOps) workflow for detecting "Shadow AI" - the unauthorized use of generative AI tools and APIs within an organization. It utilizes Google Cloud tools like BigQuery for large-scale log analysis (threat hunting) and Vertex AI's Gemini model for automated analysis and reporting. A conceptual real-time detection rule for Google Chronicle is also included.

## Tools Used

* **Google BigQuery:** For historical log analysis and threat hunting.
* **Vertex AI (Gemini Pro/Flash):** For AI-powered analysis (user-agent categorization) and executive summary generation.
* **Python:** For parsing raw log files into a usable format (CSV).
* **YARA-L (Google Chronicle - Conceptual):** For defining the real-time detection logic.

---

## Project Setup (Google Cloud)

To run this project, several Google Cloud APIs need to be enabled in your chosen project (`shadow-ai-secops-project` in this case). The primary APIs required are:

* **BigQuery API:** For data warehousing and executing SQL queries.
* **Vertex AI API:** For accessing Generative AI models.
* **Cloud Storage API:** (Implicitly used if data is staged in Cloud Storage before BigQuery).

* **Enabled APIs in Google Cloud Project:**
    ![Enabled GCP APIs Dashboard](images/gcp_apis.png)
    *(Screenshot confirming BigQuery and Vertex AI APIs are enabled)*

---

## Phase 1: Threat Hunt (BigQuery)

**Goal:** Identify historical network connections to known unapproved AI service domains using proxy logs ingested into BigQuery.

1.  **Data Preparation:** Raw proxy logs (`small-sample.log.gz`) were parsed into CSV format (`parsed_logs.csv`) using a Python script (`parse_logs.py`). This CSV was then uploaded to BigQuery.
    * **BigQuery Table Schema:**
        ![BigQuery Table Schema](images/bigquery_schema.jpg)
        *(Screenshot from: Screenshot (41).jpg)*
2.  **Hunt Query:** A SQL query (`hunt_query.sql`) was developed to search the `proxy_http_logs` table for connections to a list of AI indicators within the last 30 days, aggregating results by user, source IP, requested URL, and user agent, and summing the bytes sent.
3.  **Results:** After inserting sample data representing Shadow AI activity, the query successfully identified connections to target domains like `api.anthropic.com`, `huggingface.co`, and `chat.openai.com`. The results highlight the user, the specific URL accessed, the user agent, and notably, the volume of data sent (`total_bytes_sent`), which is a key indicator for potential data exfiltration risk.
    * **BigQuery Hunt Results:**
        ![BigQuery Hunt Query Results](images/hunt_results.jpg)
        *(Screenshot from: Screenshot (47).jpg)*

---

## Phase 2: AI-Powered Analysis (Vertex AI)

**Goal:** Utilize Vertex AI's Gemini model to automatically analyze the findings from the BigQuery hunt and generate a summary report.

1.  **User-Agent Triage:** The unique `user_agent` strings from the BigQuery results were fed into Gemini with a specific prompt (`ai_triage_prompt.txt`) asking it to categorize each as 'Web Browser', 'API/Script', or 'Unknown/Other'.
    * **Triage Prompt:**
        ![Vertex AI Triage Prompt](images/vertex_triage_prompt.jpg)
        *(Screenshot from: Screenshot (49).jpg)*
    * **Triage Output:** Gemini successfully categorized the user agents, providing insights into whether the access was interactive (browser) or potentially automated (script/API).
        ![Vertex AI Triage Output](images/vertex_triage_output.jpg)
        *(Screenshot from: Screenshot (48).jpg)*
2.  **Executive Summary Generation:** Key findings from the BigQuery hunt (top domains, users, data volume) and the user-agent triage were provided to Gemini using another prompt (`ai_summary_prompt.txt`). The model was asked to act as a SecOps GRC specialist and generate a brief executive summary for a non-technical manager, explaining Shadow AI, summarizing the findings, and highlighting the business risks (especially data exfiltration via APIs).
    * **Summary Prompt Setup:**
        ![Vertex AI Summary Prompt Setup](images/vertex_summary_setup.jpg)
        *(Screenshot from: Screenshot (53).jpg)*
    * **Summary Prompt with Findings:**
        ![Vertex AI Summary Prompt with Findings Input](images/vertex_summary_input.jpg)
        *(Screenshot from: Screenshot (52).jpg)*
    * **Generated Executive Summary (Part 1):**
        ![Vertex AI Generated Summary Output Part 1](images/vertex_summary_output_1.jpg)
        *(Screenshot from: Screenshot (50).jpg)*
    * **Generated Executive Summary (Part 2):**
        ![Vertex AI Generated Summary Output Part 2](images/vertex_summary_output_2.jpg)
        *(Screenshot from: Screenshot (51).jpg)*

---

## Phase 3: Real-Time Detection (Chronicle - Conceptual)

**Goal:** Define a detection rule to identify Shadow AI activity in real-time as logs are ingested into Google Chronicle.

**Note:** Due to the lack of direct access to a Google Chronicle instance, this phase was completed conceptually. The YARA-L rule was developed and documented but not deployed or tested live.

1.  **YARA-L Rule Development:** A YARA-L rule (`detection_rule.yaral`) was created to detect network events associated with the defined list of Shadow AI indicators.
    * **Rule Logic:** The rule inspects DNS queries, HTTP requests, and direct network connections. If the target domain or hostname matches an indicator, an alert is generated.
    * **Alert Enrichment:** The rule's `outcome` block is configured to extract key details like user information, source/destination IPs/hostnames, the specific indicator matched, log type, and data volume (if available) to provide context for SOC analysts.
2.  **Conceptual Representation:** The rule code itself serves as the artifact for this phase.
    * **Simulated Rule in Editor (Part 1 - Meta/Events):**
        ![Simulated YARA-L Rule Part 1](images/yaral_rule_part1.png)
        *(Screenshot from: Screenshot (54).png)*
    * **Simulated Rule in Editor (Part 2 - Events/Outcome/Condition):**
        ![Simulated YARA-L Rule Part 2](images/yaral_rule_part2.png)
        *(Screenshot from: Screenshot (55).jpg)*

---

## How to Run (Conceptual)

1.  **Setup:** Create a Google Cloud Project, enable BigQuery and Vertex AI APIs (as shown in the setup screenshot).
2.  **Data Ingestion:** Parse relevant network logs (e.g., proxy, DNS) into CSV format (using `parse_logs.py` or similar) and upload the data to a BigQuery table (e.g., `proxy_http_logs`). Alternatively, configure log sinks to stream data directly.
3.  **Threat Hunt:** Execute the `hunt_query.sql` in BigQuery against your log table.
4.  **AI Analysis:** Use the prompts provided (`ai_triage_prompt.txt`, `ai_summary_prompt.txt`) in Vertex AI's Generative AI Studio, inputting findings from the BigQuery results.
5.  **Real-Time Detection:** Deploy the `detection_rule.yaral` file into a Google Chronicle instance's detection engine and configure alerting actions.

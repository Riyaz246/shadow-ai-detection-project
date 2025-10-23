import gzip
import re
import csv
import sys
import os
from typing import Dict, Optional, Generator

# --- Configuration ---
LOG_FILE_PATH = 'small-sample.log.gz'
OUTPUT_CSV_PATH = 'parsed_logs.csv'

# Define the exact fields required for the CSV output
# Note: We now capture 'remote_log' as well, even if often '-'
FIELDNAMES = [
    'source_ip',
    'remote_log', # Field often represented by '-'
    'user_id',    # Field sometimes '-', sometimes a name/email
    'timestamp',
    'request_method',
    'requested_url',
    'http_status',
    'bytes_sent',
    'referrer',
    'user_agent'
]

# --- Regular Expression Definition ---
# FINAL CORRECTED PATTERN: Matches Apache Combined Log Format structure
# --- Regular Expression Definition ---
# FINAL CORRECTED PATTERN v2: Makes Referrer and User-Agent optional
LOG_PATTERN = re.compile(
    r'^(?P<source_ip>\S+)'          # %h: Source IP
    r'\s+(?P<remote_log>\S+)'       # %l: Remote logname (often '-')
    r'\s+(?P<user_id>\S+)'          # %u: Userid (often '-', sometimes a name/email)
    r'\s+\[(?P<timestamp>.*?)\]'    # %t: Timestamp
    # \"%r\": Request Method, URL, and Protocol (protocol ignored)
    r'\s+"(?P<request_method>\w+)\s+(?P<requested_url>\S+?)(?:\s+HTTP/[\d\.]+)??"'
    r'\s+(?P<http_status>[\d\-]+)'  # %>s: Status Code (allows '-')
    r'\s+(?P<bytes_sent>[\d\-]+)'   # %b: Bytes Sent (allows '-')
    # Optional Referrer and User-Agent fields: (?: ... )?
    r'(?:\s+"(?P<referrer>.*?)")?'    # Optional Referrer \"%{Referer}i\"
    r'(?:\s+"(?P<user_agent>.*?)")?$' # Optional User-Agent \"%{User-agent}i\" at end
)


def parse_log_line(line: str, line_num: int) -> Optional[Dict[str, str]]:
    """
    Attempts to match a single log line against the regex pattern.
    Returns a dictionary of extracted fields or None on failure.
    """
    try:
        match = LOG_PATTERN.match(line)
        if match:
            return match.groupdict()
        else:
            print(f"[{line_num}] WARNING: Failed to parse line (no match): {line[:100]}...") # Increased length for better debugging
            return None
    except Exception as e:
        print(f"[{line_num}] ERROR: Unexpected error while processing line: {e} | Line: {line[:100]}...")
        return None


def process_gzipped_log_file(log_path: str) -> Generator[Dict[str, str], None, None]:
    """
    Reads the gzipped log file line by line and yields parsed dictionaries.
    Handles file opening errors.
    """
    if not os.path.exists(log_path):
        print(f"CRITICAL ERROR: Input file not found at {log_path}", file=sys.stderr)
        print("Please make sure 'small-sample.log.gz' is in the same directory.", file=sys.stderr)
        sys.exit(1)

    print(f"Starting log processing for: {log_path}")

    line_num = 0
    parsed_count = 0
    error_count = 0
    try:
        with gzip.open(log_path, 'rt', encoding='utf-8', errors='ignore') as f: # Added errors='ignore' for resilience
            for line in f:
                line_num += 1
                cleaned_line = line.strip()
                if not cleaned_line:
                    continue

                parsed_data = parse_log_line(cleaned_line, line_num)

                if parsed_data:
                    parsed_count += 1
                    yield parsed_data
                else:
                    error_count += 1

    except Exception as e:
        print(f"CRITICAL ERROR: An error occurred while reading the gzip file: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Finished reading log file. Total lines read: {line_num}, Successfully parsed: {parsed_count}, Skipped/Errors: {error_count}")


def write_to_csv(data_generator: Generator[Dict[str, str], None, None], csv_path: str):
    """
    Writes the stream of parsed log dictionaries to the specified CSV file.
    """
    total_written = 0
    total_input_rows = 0 # To track how many rows were attempted to write
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
            writer.writeheader()
            print(f"Writing parsed data to {csv_path}...")

            for row in data_generator:
                total_input_rows += 1
                try:
                    # Ensure only the defined FIELDNAMES are written, preventing errors if regex captures extra groups
                    filtered_row = {key: row.get(key, '') for key in FIELDNAMES}
                    writer.writerow(filtered_row)
                    total_written += 1
                except Exception as e:
                    print(f"ERROR: Failed to write row {total_input_rows}: {e} | Row Data (partial): {str(row)[:100]}...")

    except Exception as e:
        print(f"CRITICAL ERROR: Failed to write to CSV file {csv_path}: {e}", file=sys.stderr)
        sys.exit(1)

    print("-" * 50)
    print("Processing Complete.")
    print(f"Total lines successfully parsed (from generator): {total_input_rows}") # This reflects actual parsed rows yielded
    print(f"Total lines successfully written to CSV: {total_written}")
    print(f"Output available in: {OUTPUT_CSV_PATH}")


if __name__ == '__main__':
    log_data_stream = process_gzipped_log_file(LOG_FILE_PATH)
    write_to_csv(log_data_stream, OUTPUT_CSV_PATH)
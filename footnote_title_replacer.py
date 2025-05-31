# -----------------------------------------------------------------------------
# Script Name: footnote_title_replacer.py
#
# Purpose:
# This script processes a Markdown (.md) file converted from HTML using Pandoc.
# It performs the following transformations:
#   - Inserts a visible comma between adjacent footnote markers.
#   - Replaces raw URL footnotes (e.g., [^1]: http://example.com) with
#     Markdown links including the page or PDF title.
#   - Logs any errors encountered when fetching URLs.
#   - Optionally uses Cloudscraper to bypass Cloudflare protections.
#
# Usage:
#   python script.py input.md output.md [--debug] [--cloudscraper]
# -----------------------------------------------------------------------------

import sys
import re
import requests
import cloudscraper
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from io import BytesIO
from datetime import datetime

# --- Logging setup ---
today = datetime.now()
date_str = today.strftime('%Y-%m-%d')
time_str = today.strftime('%Y-%m-%d-%H-%M')
error_log_path = f"errors-{time_str}.txt"
error_count = 0
comma_count = 0
footnote_count = 0
processed_links = 0

debug_mode = False
use_cloudscraper = False
scraper = None

# Log a message to console, optionally only in debug mode
def log(msg):
    if debug_mode:
        print(msg)
    else:
        print(f"Processed footnotes: {footnote_count}, links: {processed_links}, errors: {error_count}\r", end="")

# Fetch and return the title of a webpage or PDF given a URL.
# If an error occurs, log it and return a placeholder title.
def get_title_from_url(url, original_footnote):
    global error_count
    log(f"Fetching title for URL: {url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = scraper.get(url, headers=headers, timeout=10) if use_cloudscraper else requests.get(url, headers=headers, timeout=10)
        content_type = response.headers.get('Content-Type', '')
        log(f"Content-Type: {content_type}")

        if 'application/pdf' in content_type:
            reader = PdfReader(BytesIO(response.content))
            title = reader.metadata.title or 'Untitled PDF'
        elif 'text/html' in content_type:
            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.find('title')
            title = title_tag.text.strip() if title_tag else 'Untitled Webpage'
            if title.lower().startswith("verifying if your connection") or "cloudflare" in title.lower():
                raise ValueError("Bot protection page detected")
        else:
            error_count += 1
            with open(error_log_path, 'a', encoding='utf-8') as logf:
                logf.write(f"Unknown content type for URL {url}: {content_type}\n")
                logf.write(f"Original footnote: {original_footnote}\n")
            log(f"Unknown content type for URL {url}")
            return 'Unknown Resource'

        if title.strip().lower() == "verifying if your connection is secure...":
            raise ValueError("Detected bot protection title")

        log(f"Retrieved title: {title}")
        return title
    except Exception as e:
        error_count += 1
        with open(error_log_path, 'a', encoding='utf-8') as logf:
            logf.write(f"Error retrieving title from {url}: {e}\n")
            logf.write(f"Original footnote: {original_footnote}\n")
        log(f"Error retrieving title from {url}: {e}")
        return "Error retrieving title"

# Process a Markdown file:
# - Inserts commas between adjacent footnote markers.
# - Replaces URL footnotes with titled Markdown links.
# - Writes output to a new file and prints summary statistics.
def process_markdown(input_path, output_path):
    global comma_count, footnote_count, processed_links
    log(f"Reading input file: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    log("Original content loaded.")

    # Step 1: Insert <sup>,</sup> between adjacent footnote markers
    content, comma_count = re.subn(r'(\[\^.+?\])(\[\^)', r'\1<sup>,</sup>\2', content)
    log(f"Inserted <sup>,</sup> between adjacent footnotes: {comma_count} replacements made.")

    # Step 2: Replace plain footnotes pointing directly to HTTP URLs
    def replace_footnote(match):
        global footnote_count, processed_links
        label = match.group(1)
        url = match.group(2).strip()
        original_footnote = match.group(0)
        footnote_count += 1
        log(f"Processing footnote: [^{label}]: {url}")
        title = get_title_from_url(url, original_footnote)
        processed_links += 1
        new_footnote = f"[^{label}]: [{title}]({url}) retrieved on {date_str}"
        log(f"Updated footnote: {new_footnote}")
        return new_footnote

    # Matches: [^label]: http(s)://example.com
    content, _ = re.subn(r'\[\^(.+?)\]:\s+(https?://\S+)', replace_footnote, content)

    log(f"Writing output to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("\nDone.")
    print(f"Summary:")
    print(f" - Footnote commas inserted: {comma_count}")
    print(f" - Footnote links updated: {processed_links}")
    print(f" - Errors encountered: {error_count}")
    if error_count:
        print(f" - Errors logged to: {error_log_path}")

# Entry point: handles argument parsing and triggers the main processing
if __name__ == '__main__':
    args = sys.argv[1:]
    if not (2 <= len(args) <= 4):
        print("Usage: python script.py input.md output.md [--debug] [--cloudscraper]")
        sys.exit(1)

    input_file = args[0]
    output_file = args[1]
    debug_mode = '--debug' in args
    use_cloudscraper = '--cloudscraper' in args

    if use_cloudscraper:
        scraper = cloudscraper.create_scraper()

    process_markdown(input_file, output_file)
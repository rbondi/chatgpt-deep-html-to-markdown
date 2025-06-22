#!/bin/bash

# -----------------------------------------------------------------------------
# Script: convert.sh
# Purpose: Process an HTML file in ./inputs/ through a pipeline and convert it to Markdown
#          using custom preprocessing, Lua filtering, and footnote postprocessing.
# Updated: 2025-06-22 - Simplified to require only one argument (filename.html)
# -----------------------------------------------------------------------------

set -e

# --- Parse single argument ---
BASENAME="$1"

if [[ -z "$BASENAME" ]]; then
  echo "Usage: $0 filename.html"
  exit 1
fi

INPUT_FILE="inputs/$BASENAME"
OUTPUT_PREFIX="${BASENAME%.html}"

if [[ ! -f "$INPUT_FILE" ]]; then
  echo "Error: Input file '$INPUT_FILE' not found in ./inputs/"
  exit 1
fi

# --- Validate required directories ---
PIPELINE_DIR="./pipeline_files"
OUTPUT_DIR="./outputs"

[[ -d "$PIPELINE_DIR" ]] || { echo "Error: '$PIPELINE_DIR' does not exist."; exit 1; }
[[ -d "$OUTPUT_DIR" ]]   || { echo "Error: '$OUTPUT_DIR' does not exist."; exit 1; }

# --- Activate Python virtual environment ---
if [[ -z "$VIRTUAL_ENV" ]]; then
  if [[ -d "venv" ]]; then
    echo "Activating Python virtual environment: venv"
    source venv/bin/activate
  else
    echo "Error: not in a virtualenv and no 'venv' directory found"
    exit 1
  fi
fi

# --- Step 1: Clean HTML ---
echo "[Step 1/4] Cleaning input HTML with clean_html.py..."
CLEAN_HTML="${PIPELINE_DIR}/out-${OUTPUT_PREFIX}-clean.html"
python clean_html.py "$INPUT_FILE" "$CLEAN_HTML"
echo "[Step 1/4] Done: Cleaned HTML saved to $CLEAN_HTML"

# --- Step 2: Convert HTML to Markdown with Pandoc ---
echo "[Step 2/4] Converting cleaned HTML to Markdown using Pandoc..."
RAW_MD="${PIPELINE_DIR}/out-${OUTPUT_PREFIX}-raw.md"
pandoc "$CLEAN_HTML" -f html -t markdown \
  --lua-filter=clean.lua -o "$RAW_MD"
echo "[Step 2/4] Done: Raw Markdown saved to $RAW_MD"

# --- Step 3: Resolve footnotes and page titles ---
echo "[Step 3/4] Resolving footnotes and replacing URLs with titles..."
FINAL_MD_TEMP="${PIPELINE_DIR}/out-${OUTPUT_PREFIX}.md"
python footnote_title_replacer.py "$RAW_MD" "$FINAL_MD_TEMP" --cloudscraper
echo "[Step 3/4] Done: Footnotes processed into $FINAL_MD_TEMP"

# --- Step 4: Save final output, handle overwrite ---
echo "[Step 4/4] Saving final Markdown to ./outputs..."
FINAL_MD_DEST="${OUTPUT_DIR}/out-${OUTPUT_PREFIX}.md"
if [[ -f "$FINAL_MD_DEST" ]]; then
  timestamp=$(date +"%Y-%m-%d-%H-%M")
  BACKUP_NAME="out-${OUTPUT_PREFIX}-${timestamp}.md"
  mv "$FINAL_MD_DEST" "${OUTPUT_DIR}/$BACKUP_NAME"
  echo "Existing output file renamed to: $BACKUP_NAME"
fi

mv "$FINAL_MD_TEMP" "$FINAL_MD_DEST"
echo "[Step 4/4] Done: Final output written to $FINAL_MD_DEST"

echo "✅ Pipeline completed successfully."
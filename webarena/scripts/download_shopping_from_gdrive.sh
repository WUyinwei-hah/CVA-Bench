#!/usr/bin/env bash
set -euo pipefail

TAR_PATH="${1:-/Volumes/外置硬盘/docker/shopping_final_0712.tar}"
FILE_ID="${2:-1gxXalk9O0p9eu1YkIJcmZta1nvvyAJpA}"
AUTHUSER="${AUTHUSER:-0}"
TOTAL_BYTES="${TOTAL_BYTES:-67575898112}"
CHUNK_BYTES="${CHUNK_BYTES:-33554432}"
MIN_CHUNK_BYTES="${MIN_CHUNK_BYTES:-1048576}"

BASE_URL="https://drive.usercontent.google.com/download"
QUERY_URL="${BASE_URL}?id=${FILE_ID}&export=download&authuser=${AUTHUSER}"

mkdir -p "$(dirname "$TAR_PATH")"
ACTIVE_CHUNK_BYTES="$CHUNK_BYTES"

while true; do
  CURRENT_BYTES="0"
  if [[ -f "$TAR_PATH" ]]; then
    CURRENT_BYTES="$(stat -f '%z' "$TAR_PATH")"
  fi

  if [[ "$CURRENT_BYTES" -ge "$TOTAL_BYTES" ]]; then
    echo "download complete: $CURRENT_BYTES / $TOTAL_BYTES"
    exit 0
  fi

  TMP_HTML="$(mktemp /tmp/shopping_gdrive_confirm.XXXXXX.html)"
  TMP_CHUNK="$(mktemp /tmp/shopping_gdrive_chunk.XXXXXX.bin)"
  TMP_META="$(mktemp /tmp/shopping_gdrive_meta.XXXXXX.txt)"
  cleanup() {
    rm -f "$TMP_HTML" "$TMP_CHUNK" "$TMP_META"
  }
  trap cleanup EXIT

  SUCCESS=0
  ATTEMPT_CHUNK_BYTES="$ACTIVE_CHUNK_BYTES"

  while [[ "$SUCCESS" -eq 0 ]]; do
    rm -f "$TMP_HTML" "$TMP_CHUNK" "$TMP_META"

    curl -L -sS "$QUERY_URL" -o "$TMP_HTML"

    UUID_VALUE="$(
      python3 - "$TMP_HTML" <<'PY'
import re
import sys
from pathlib import Path

html = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
match = re.search(r'name="uuid" value="([^"]+)"', html)
if not match:
    raise SystemExit("Failed to extract Google Drive uuid from confirmation page.")
print(match.group(1))
PY
    )"

    CONFIRMED_URL="${BASE_URL}?id=${FILE_ID}&export=download&authuser=${AUTHUSER}&confirm=t&uuid=${UUID_VALUE}"

    RANGE_START="$CURRENT_BYTES"
    RANGE_END=$((CURRENT_BYTES + ATTEMPT_CHUNK_BYTES - 1))
    if [[ "$RANGE_END" -ge "$TOTAL_BYTES" ]]; then
      RANGE_END=$((TOTAL_BYTES - 1))
    fi
    EXPECTED_BYTES=$((RANGE_END - RANGE_START + 1))

    echo "resume_from: $CURRENT_BYTES"
    echo "range: ${RANGE_START}-${RANGE_END}"
    echo "chunk_bytes: ${ATTEMPT_CHUNK_BYTES}"

    curl -L --progress-bar \
      --range "${RANGE_START}-${RANGE_END}" \
      --output "$TMP_CHUNK" \
      --write-out "HTTP:%{http_code}\nCTYPE:%{content_type}\nSIZE:%{size_download}\n" \
      "$CONFIRMED_URL" > "$TMP_META"

    HTTP_CODE="$(awk -F: '/^HTTP:/{print $2}' "$TMP_META" | tail -n 1 | tr -d '\r')"
    CONTENT_TYPE="$(awk -F: '/^CTYPE:/{sub(/^:/, "", $0); print substr($0, 7)}' "$TMP_META" | tail -n 1 | tr -d '\r')"
    DOWNLOADED_BYTES="$(awk -F: '/^SIZE:/{print $2}' "$TMP_META" | tail -n 1 | tr -d '\r')"
    ACTUAL_CHUNK_BYTES="$(stat -f '%z' "$TMP_CHUNK" 2>/dev/null || echo 0)"

    if [[ "$HTTP_CODE" == "206" && "$CONTENT_TYPE" == "application/octet-stream" && "$ACTUAL_CHUNK_BYTES" == "$EXPECTED_BYTES" ]]; then
      SUCCESS=1
      ACTIVE_CHUNK_BYTES="$ATTEMPT_CHUNK_BYTES"
      break
    fi

    echo "retrying with smaller chunk: HTTP=$HTTP_CODE CTYPE=$CONTENT_TYPE expected=$EXPECTED_BYTES actual=$ACTUAL_CHUNK_BYTES reported=$DOWNLOADED_BYTES" >&2

    if [[ "$ATTEMPT_CHUNK_BYTES" -le "$MIN_CHUNK_BYTES" ]]; then
      echo "Failed even at minimum chunk size ${MIN_CHUNK_BYTES}." >&2
      exit 1
    fi

    ATTEMPT_CHUNK_BYTES=$((ATTEMPT_CHUNK_BYTES / 2))
    if [[ "$ATTEMPT_CHUNK_BYTES" -lt "$MIN_CHUNK_BYTES" ]]; then
      ATTEMPT_CHUNK_BYTES="$MIN_CHUNK_BYTES"
    fi
  done

  cat "$TMP_CHUNK" >> "$TAR_PATH"

  NEW_BYTES="$(stat -f '%z' "$TAR_PATH")"
  echo "current_size: $NEW_BYTES"

  rm -f "$TMP_HTML" "$TMP_CHUNK" "$TMP_META"
  trap - EXIT

  if [[ "$NEW_BYTES" -le "$CURRENT_BYTES" ]]; then
    echo "No progress made while resuming from Google Drive." >&2
    exit 1
  fi

  sleep 1
done

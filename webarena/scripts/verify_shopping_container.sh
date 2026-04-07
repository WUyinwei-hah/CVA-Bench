#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-7770}"
URL="http://localhost:${PORT}"

echo "Checking ${URL}"
curl -I --max-time 15 "$URL"


#!/usr/bin/env bash
set -euo pipefail

TAR_PATH="${1:-/Volumes/外置硬盘/docker/shopping_final_0712.tar}"
TOTAL_BYTES="67575898112"

if [[ ! -f "$TAR_PATH" ]]; then
  echo "missing: $TAR_PATH"
  exit 1
fi

CURRENT_BYTES="$(stat -f '%z' "$TAR_PATH")"

python3 - "$CURRENT_BYTES" "$TOTAL_BYTES" "$TAR_PATH" <<'PY'
import sys
from pathlib import Path

current = int(sys.argv[1])
total = int(sys.argv[2])
path = Path(sys.argv[3])

percent = (current / total) * 100 if total else 0.0
gib = current / (1024 ** 3)
total_gib = total / (1024 ** 3)

print(f"path: {path}")
print(f"downloaded: {current} bytes ({gib:.2f} GiB)")
print(f"total: {total} bytes ({total_gib:.2f} GiB)")
print(f"progress: {percent:.2f}%")
PY


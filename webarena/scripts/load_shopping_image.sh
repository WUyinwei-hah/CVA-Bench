#!/usr/bin/env bash
set -euo pipefail

TAR_PATH="${1:-/Volumes/外置硬盘/docker/shopping_final_0712.tar}"

if [[ ! -f "$TAR_PATH" ]]; then
  echo "missing image tar: $TAR_PATH"
  exit 1
fi

echo "Loading Docker image from: $TAR_PATH"
docker load --input "$TAR_PATH"


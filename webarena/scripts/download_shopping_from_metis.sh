#!/usr/bin/env bash
set -euo pipefail

TAR_PATH="${1:-/Volumes/外置硬盘/docker/shopping_final_0712.tar}"
SOURCE_URL="${2:-http://metis.lti.cs.cmu.edu/webarena-images/shopping_final_0712.tar}"

mkdir -p "$(dirname "$TAR_PATH")"
curl -L -C - --progress-bar "$SOURCE_URL" -o "$TAR_PATH"

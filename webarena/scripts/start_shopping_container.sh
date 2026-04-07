#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="${CONTAINER_NAME:-shopping}"
IMAGE_NAME="${IMAGE_NAME:-shopping_final_0712}"
PORT="${PORT:-7770}"

if docker ps -a --format '{{.Names}}' | rg -x "$CONTAINER_NAME" >/dev/null 2>&1; then
  echo "Container $CONTAINER_NAME already exists. Starting it."
  docker start "$CONTAINER_NAME"
  exit 0
fi

echo "Starting $CONTAINER_NAME from $IMAGE_NAME on port $PORT"
docker run --name "$CONTAINER_NAME" -p "${PORT}:80" -d "$IMAGE_NAME"


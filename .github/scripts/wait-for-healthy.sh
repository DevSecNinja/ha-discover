#!/bin/bash
# Wait for a Docker container to become healthy
# Usage: wait-for-healthy.sh <container-name> [timeout-seconds]

set -e

CONTAINER_NAME="${1}"
TIMEOUT="${2:-60}"

if [ -z "$CONTAINER_NAME" ]; then
    echo "Usage: $0 <container-name> [timeout-seconds]"
    exit 1
fi

echo "Waiting for $CONTAINER_NAME container to be healthy..."
elapsed=0

while [ $elapsed -lt $TIMEOUT ]; do
    if [ "$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null)" = "healthy" ]; then
        echo "✓ $CONTAINER_NAME container is healthy"
        exit 0
    fi
    echo "Waiting... ($elapsed seconds)"
    sleep 5
    elapsed=$((elapsed + 5))
done

echo "✗ $CONTAINER_NAME container health check timeout"
docker logs "$CONTAINER_NAME"
exit 1

#!/bin/bash
# Start backend Docker container for testing
# Usage: start-backend-container.sh <container-name> <image-tag> <port>

set -e

CONTAINER_NAME="${1}"
IMAGE_TAG="${2}"
PORT="${3:-8000}"

if [ -z "$CONTAINER_NAME" ] || [ -z "$IMAGE_TAG" ]; then
    echo "Usage: $0 <container-name> <image-tag> [port]"
    exit 1
fi

echo "Starting backend container ${CONTAINER_NAME} from image ${IMAGE_TAG}..."

docker run -d \
  --name "${CONTAINER_NAME}" \
  -p "${PORT}:8000" \
  -e ENVIRONMENT=development \
  "${IMAGE_TAG}"

echo "✓ Backend container ${CONTAINER_NAME} started"

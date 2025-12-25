#!/bin/bash
# Start Docker container
# Usage: start-container.sh <container-name> <image-tag> <port-mapping> [additional-docker-run-args...]

set -e

CONTAINER_NAME="${1}"
IMAGE_TAG="${2}"
PORT_MAPPING="${3}"
shift 3
ADDITIONAL_ARGS="$@"

if [ -z "$CONTAINER_NAME" ] || [ -z "$IMAGE_TAG" ]; then
    echo "Usage: $0 <container-name> <image-tag> <port-mapping> [additional-docker-run-args...]"
    exit 1
fi

echo "Starting container $CONTAINER_NAME from image $IMAGE_TAG..."

docker run -d --name "$CONTAINER_NAME" \
    -p "$PORT_MAPPING" \
    $ADDITIONAL_ARGS \
    "$IMAGE_TAG"

echo "✓ Container $CONTAINER_NAME started"

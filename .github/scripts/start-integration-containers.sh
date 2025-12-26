#!/bin/bash
# Start both backend and frontend containers for integration testing
# Usage: start-integration-containers.sh <backend-image> <frontend-image>

set -e

BACKEND_IMAGE="${1}"
FRONTEND_IMAGE="${2}"

if [ -z "$BACKEND_IMAGE" ] || [ -z "$FRONTEND_IMAGE" ]; then
    echo "Usage: $0 <backend-image> <frontend-image>"
    exit 1
fi

echo "Starting backend container..."
docker run -d \
  --name ha-discover-backend \
  -p 8000:8000 \
  -e ENVIRONMENT=development \
  "${BACKEND_IMAGE}"

echo "Starting frontend container..."
.github/scripts/start-container.sh ha-discover-frontend "${FRONTEND_IMAGE}" 3000:80

echo "Waiting for both containers to be healthy..."
sleep 10

echo "✓ Both containers started"

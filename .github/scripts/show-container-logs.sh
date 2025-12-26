#!/bin/bash
# Show container logs for debugging
# Usage: show-container-logs.sh <backend-container> <frontend-container>

set -e

BACKEND_CONTAINER="${1:-ha-discover-backend}"
FRONTEND_CONTAINER="${2:-ha-discover-frontend}"

echo "=== Backend logs ==="
docker logs "${BACKEND_CONTAINER}" 2>&1 || echo "Backend container not found"

echo ""
echo "=== Frontend logs ==="
docker logs "${FRONTEND_CONTAINER}" 2>&1 || echo "Frontend container not found"

#!/bin/bash
# Test index-now command in container
# Usage: test-index-now.sh <container-name>

set -e

CONTAINER_NAME="${1}"

if [ -z "$CONTAINER_NAME" ]; then
    echo "Usage: $0 <container-name>"
    exit 1
fi

echo "Testing index-now command in container..."

# Test that index-now command exists and is executable
docker exec "${CONTAINER_NAME}" which index-now

# Test that index-now command can be invoked directly
# (Note: This will fail indexing due to no GitHub token, but should start correctly)
docker exec "${CONTAINER_NAME}" timeout 10 index-now 2>&1 | head -20 || true

# Verify the command started the indexing process
if docker exec "${CONTAINER_NAME}" timeout 10 index-now 2>&1 | grep -q "Starting indexing job"; then
  echo "✓ index-now command executed successfully"
else
  echo "✗ index-now command failed to start"
  exit 1
fi

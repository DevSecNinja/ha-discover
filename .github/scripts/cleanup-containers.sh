#!/bin/bash
# Cleanup Docker containers
# Usage: cleanup-containers.sh <container1> [container2] [container3...]

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <container1> [container2] [container3...]"
    exit 1
fi

for CONTAINER in "$@"; do
    echo "Removing container ${CONTAINER}..."
    docker rm -f "${CONTAINER}" 2>&1 || true
done

echo "✓ Cleanup complete"

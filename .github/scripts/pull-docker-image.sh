#!/bin/bash
set -euo pipefail

# Pull a Docker image from the registry
# Usage: ./pull-docker-image.sh <registry> <image_name> <digest>

REGISTRY=$1
IMAGE_NAME=$2
DIGEST=$3

IMAGE_NAME_LOWER=$(echo "${REGISTRY}/${IMAGE_NAME}" | tr '[:upper:]' '[:lower:]')
docker pull ${IMAGE_NAME_LOWER}@${DIGEST}

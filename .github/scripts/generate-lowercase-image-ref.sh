#!/bin/bash
set -euo pipefail

# Generate a lowercase Docker image reference
# Usage: ./generate-lowercase-image-ref.sh <registry> <image_name> <digest>

REGISTRY=$1
IMAGE_NAME=$2
DIGEST=$3

IMAGE_REF=$(echo "${REGISTRY}/${IMAGE_NAME}@${DIGEST}" | tr '[:upper:]' '[:lower:]')
echo "ref=${IMAGE_REF}"

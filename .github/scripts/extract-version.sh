#!/bin/bash
# Extract version from git reference or workflow input
# Usage: extract-version.sh <event_name> <input_version> <git_ref>

set -e

EVENT_NAME="${1}"
INPUT_VERSION="${2}"
GIT_REF="${3}"

if [ -z "$EVENT_NAME" ] || [ -z "$GIT_REF" ]; then
    echo "Usage: $0 <event_name> <input_version> <git_ref>"
    exit 1
fi

if [ "$EVENT_NAME" = "workflow_dispatch" ]; then
    VERSION="${INPUT_VERSION}"
    VERSION_TAG="v${VERSION}"
else
    # Extract version from tag (e.g., v1.0.0 -> 1.0.0)
    VERSION=${GIT_REF#refs/tags/v}
    VERSION_TAG=${GIT_REF#refs/tags/}
fi

echo "version=${VERSION}"
echo "version_tag=${VERSION_TAG}"

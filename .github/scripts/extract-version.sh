#!/bin/bash
# Extract version from git reference or workflow input
# Usage: extract-version.sh <event_name> <pr_number> <git_ref>

set -e

EVENT_NAME="${1}"
PR_NUMBER="${2}"
GIT_REF="${3}"

if [ "$EVENT_NAME" = "pull_request" ]; then
    # For PRs, use format: 0.0.0-pr.<number>.<short-sha>
    if [ -z "$PR_NUMBER" ]; then
        echo "Error: PR_NUMBER required for pull_request event"
        exit 1
    fi
    SHORT_SHA=$(git rev-parse --short HEAD)
    VERSION="0.0.0-pr.${PR_NUMBER}.${SHORT_SHA}"
    VERSION_TAG="pr-${PR_NUMBER}"
elif [ "$EVENT_NAME" = "workflow_dispatch" ]; then
    if [ -z "$INPUT_VERSION" ]; then
        echo "Error: version input required for workflow_dispatch event"
        exit 1
    fi
    VERSION="${PR_NUMBER}" # PR_NUMBER is actually INPUT_VERSION for workflow_dispatch
    VERSION_TAG="v${VERSION}"
elif [ -n "$GIT_REF" ]; then
    # Extract version from tag (e.g., v1.0.0 -> 1.0.0)
    VERSION=${GIT_REF#refs/tags/v}
    VERSION_TAG=${GIT_REF#refs/tags/}
else
    echo "Error: Invalid arguments for event $EVENT_NAME"
    exit 1
fi

echo "version=${VERSION}"
echo "version_tag=${VERSION_TAG}"

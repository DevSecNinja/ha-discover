#!/bin/bash
# Update frontend package.json version
# Usage: update-frontend-version.sh <version>

set -e

VERSION="${1}"

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

cd frontend

echo "Updating frontend version to ${VERSION}..."
npm version "${VERSION}" --no-git-tag-version

echo "✓ Frontend version updated in package.json"

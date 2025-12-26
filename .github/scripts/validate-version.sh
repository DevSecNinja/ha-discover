#!/bin/bash
# Validate version number format (semantic versioning)
# Usage: validate-version.sh <version>

set -e

VERSION="${1}"

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

# Check if version matches semantic versioning format (X.Y.Z or X.Y.Z-suffix)
if ! echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9\.]+)?$'; then
    echo "✗ Invalid version format: $VERSION"
    echo "Version must follow semantic versioning (e.g., 1.0.0, 1.2.3-beta.1)"
    exit 1
fi

echo "✓ Version format is valid: $VERSION"

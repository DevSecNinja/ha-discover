#!/bin/bash
# Update backend version file
# Usage: update-backend-version.sh <version>

set -e

VERSION="${1}"

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

VERSION_FILE="backend/app/version.py"

echo "Updating backend version to ${VERSION}..."

cat > "$VERSION_FILE" << EOF
"""Version information for hadiscover backend."""

__version__ = "${VERSION}"
EOF

echo "✓ Backend version updated in ${VERSION_FILE}"

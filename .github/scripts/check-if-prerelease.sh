#!/bin/bash
set -euo pipefail

# Check if a version should be marked as prerelease
# Usage: ./check-if-prerelease.sh <version> <manual_prerelease_flag>

VERSION=$1
MANUAL_PRERELEASE=${2:-false}

# Extract version without v prefix
VERSION_NUM=$(echo "$VERSION" | grep -oP '\d+\.\d+\.\d+.*' || echo "$VERSION")

# Check if version contains prerelease identifiers or if manually set
if [[ "$MANUAL_PRERELEASE" == "true" ]] || [[ "$VERSION_NUM" =~ -alpha|-beta|-rc|-pre ]]; then
  echo "is_prerelease=true"
else
  echo "is_prerelease=false"
fi

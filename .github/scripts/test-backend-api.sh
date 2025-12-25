#!/bin/bash
# Test backend API endpoints
# Usage: test-backend-api.sh [port]

set -e

PORT="${1:-8000}"
BASE_URL="http://localhost:${PORT}"

echo "Testing API endpoints on ${BASE_URL}..."

# Test root endpoint
echo "Testing root endpoint..."
root_response=$(curl -s "${BASE_URL}/")
echo "Root endpoint response: $root_response"
if ! echo "$root_response" | grep -q "hadiscover API"; then
    echo "✗ Root endpoint test failed"
    exit 1
fi
echo "✓ Root endpoint works"

# Test health endpoint
echo "Testing health endpoint..."
health_response=$(curl -s "${BASE_URL}/api/v1/health")
echo "Health endpoint response: $health_response"
if ! echo "$health_response" | grep -q "healthy"; then
    echo "✗ Health endpoint test failed"
    exit 1
fi
echo "✓ Health endpoint works"

# Test version in root endpoint
echo "Testing version field..."
if ! echo "$root_response" | grep -q "version"; then
    echo "✗ Version field not found in root endpoint"
    exit 1
fi
echo "✓ Version field present"

# Test statistics endpoint
echo "Testing statistics endpoint..."
response=$(curl -s "${BASE_URL}/api/v1/statistics")
echo "Statistics endpoint response: $response"
if ! echo "$response" | grep -q "total_repositories"; then
    echo "✗ Statistics endpoint test failed"
    exit 1
fi
echo "✓ Statistics endpoint works"

# Test search endpoint
echo "Testing search endpoint..."
response=$(curl -s "${BASE_URL}/api/v1/search?q=test")
echo "Search endpoint response: $response"
if ! echo "$response" | grep -q "results"; then
    echo "✗ Search endpoint test failed"
    exit 1
fi
echo "✓ Search endpoint works"

# Test OpenAPI docs endpoint
echo "Testing OpenAPI docs endpoint..."
status=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/docs")
if [ "$status" != "200" ]; then
    echo "✗ OpenAPI docs endpoint returned status $status"
    exit 1
fi
echo "✓ OpenAPI docs endpoint works"

echo "✓ All backend API tests passed"

#!/bin/bash
# Test frontend web server
# Usage: test-frontend.sh [port]

set -e

PORT="${1:-3000}"
BASE_URL="http://localhost:${PORT}"

echo "Testing frontend web server on ${BASE_URL}..."

# Test root endpoint
echo "Testing root endpoint..."
status=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/")
if [ "$status" != "200" ]; then
    echo "✗ Frontend root endpoint returned status $status"
    exit 1
fi
echo "✓ Frontend root endpoint works (status: $status)"

# Test that HTML is served
echo "Testing HTML content..."
response=$(curl -s "${BASE_URL}/")
if ! echo "$response" | grep -q "<!DOCTYPE html>"; then
    echo "✗ Frontend does not serve HTML"
    exit 1
fi
echo "✓ Frontend serves HTML correctly"

# Test security headers
echo "Testing security headers..."
headers=$(curl -s -I "${BASE_URL}/")

if ! echo "$headers" | grep -qi "X-Frame-Options"; then
    echo "✗ X-Frame-Options header missing"
    exit 1
fi
echo "✓ X-Frame-Options header present"

if ! echo "$headers" | grep -qi "X-Content-Type-Options"; then
    echo "✗ X-Content-Type-Options header missing"
    exit 1
fi
echo "✓ X-Content-Type-Options header present"

if ! echo "$headers" | grep -qi "Content-Security-Policy"; then
    echo "✗ Content-Security-Policy header missing"
    exit 1
fi
echo "✓ Content-Security-Policy header present"

# Test health endpoint
echo "Testing health endpoint..."
health_status=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health.html")
if [ "$health_status" != "200" ]; then
    echo "✗ Health endpoint returned status $health_status"
    exit 1
fi
echo "✓ Health endpoint works (status: $health_status)"

# Test 404 handling for invalid paths
echo "Testing 404 handling..."
not_found_status=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/this-page-does-not-exist")
if [ "$not_found_status" != "404" ]; then
    echo "✗ Invalid path returned status $not_found_status instead of 404"
    exit 1
fi
echo "✓ 404 handling works correctly"

echo "✓ All frontend tests passed"

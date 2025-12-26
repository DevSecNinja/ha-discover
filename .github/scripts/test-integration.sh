#!/bin/bash
# Run integration tests on backend and frontend containers
# Usage: test-integration.sh

set -e

echo "Testing that both services are running together..."

# Test backend is accessible
backend_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health)
if [ "$backend_status" != "200" ]; then
  echo "✗ Backend not accessible (status: $backend_status)"
  exit 1
fi
echo "✓ Backend accessible"

# Test frontend is accessible
frontend_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/)
if [ "$frontend_status" != "200" ]; then
  echo "✗ Frontend not accessible (status: $frontend_status)"
  exit 1
fi
echo "✓ Frontend accessible"

# Test index-now command in backend container
echo "Testing index-now command..."
if docker exec ha-discover-backend which index-now > /dev/null 2>&1; then
  echo "✓ index-now command found in PATH"
else
  echo "✗ index-now command not found in PATH"
  exit 1
fi

# Test that index-now can be executed
if docker exec ha-discover-backend timeout 5 index-now 2>&1 | grep -q "Starting indexing job"; then
  echo "✓ index-now command executes correctly"
else
  echo "✗ index-now command failed to execute"
  exit 1
fi

echo "✓ Integration test passed - both services running successfully"

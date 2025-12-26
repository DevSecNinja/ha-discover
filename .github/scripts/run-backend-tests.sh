#!/bin/bash
# Run backend tests
# Usage: run-backend-tests.sh

set -e

cd backend

echo "Running backend tests..."
pytest tests/ -v --tb=short

echo "✓ Backend tests passed"

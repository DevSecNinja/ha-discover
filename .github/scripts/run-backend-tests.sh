#!/bin/bash
# Run backend tests
# Usage: run-backend-tests.sh

set -e

cd backend

echo "Running backend tests with coverage..."
pytest tests/ -v --tb=short --cov --cov-branch --cov-report=xml --cov-report=term --junitxml=junit.xml -o junit_family=legacy

echo "✓ Backend tests passed"

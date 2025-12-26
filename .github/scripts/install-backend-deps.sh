#!/bin/bash
# Install backend dependencies
# Usage: install-backend-deps.sh

set -e

cd backend

echo "Upgrading pip..."
python -m pip install --upgrade pip

echo "Installing backend dependencies..."
pip install -r requirements.txt

echo "✓ Backend dependencies installed"

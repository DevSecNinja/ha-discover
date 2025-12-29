#!/bin/bash

# HA Discover - Setup Script
# This script sets up all prerequisites for running the application

set -e  # Exit on error

echo "======================================"
echo "HA Discover - Setup"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python 3.12+ is available
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
echo ""

# Check if Node.js is available
echo "Checking Node.js version..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js is not installed${NC}"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js $NODE_VERSION found${NC}"
echo ""

# Setup Backend
echo "======================================"
echo "Setting up Backend..."
echo "======================================"
echo ""

cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo "Installing backend dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    echo -e "${GREEN}✓ Backend dependencies installed${NC}"
else
    echo -e "${RED}✗ requirements.txt not found${NC}"
    exit 1
fi

# Create data directory if it doesn't exist
if [ ! -d "data" ]; then
    mkdir data
    echo -e "${GREEN}✓ Data directory created${NC}"
fi

# Deactivate virtual environment
deactivate

cd ..
echo ""

# Setup Frontend
echo "======================================"
echo "Setting up Frontend..."
echo "======================================"
echo ""

cd frontend

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo -e "${RED}✗ package.json not found${NC}"
    exit 1
fi

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
else
    echo -e "${YELLOW}node_modules already exists, checking for updates...${NC}"
    npm install
    echo -e "${GREEN}✓ Frontend dependencies up to date${NC}"
fi

cd ..
echo ""

# Final summary
echo "======================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "======================================"
echo ""
echo "Backend setup:"
echo "  ✓ Virtual environment created"
echo "  ✓ Dependencies installed"
echo "  ✓ Data directory ready"
echo ""
echo "Frontend setup:"
echo "  ✓ Dependencies installed"
echo ""
echo "You can now start the application with:"
echo "  ./start.sh"
echo ""
echo "Or manually:"
echo "  Backend:  cd backend && source venv/bin/activate && python -m uvicorn app.main:app --reload"
echo "  Frontend: cd frontend && npm run dev"
echo ""

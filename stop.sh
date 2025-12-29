#!/bin/bash

# HA Discover - Stop Script
# This script stops both backend and frontend servers

echo "Stopping HA Discover..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Find and stop backend (uvicorn)
echo "Stopping Backend API..."
BACKEND_PIDS=$(pgrep -f "uvicorn app.main:app")
if [ -n "$BACKEND_PIDS" ]; then
    echo "Found backend process(es): $BACKEND_PIDS"
    kill $BACKEND_PIDS 2>/dev/null
    sleep 1
    # Force kill if still running
    if pgrep -f "uvicorn app.main:app" > /dev/null; then
        echo "Force stopping backend..."
        pkill -9 -f "uvicorn app.main:app"
    fi
    echo -e "${GREEN}✓ Backend stopped${NC}"
else
    echo -e "${YELLOW}No backend process found${NC}"
fi

echo ""

# Find and stop frontend (next dev / npm)
echo "Stopping Frontend..."
FRONTEND_PIDS=$(pgrep -f "next dev")
if [ -n "$FRONTEND_PIDS" ]; then
    echo "Found frontend process(es): $FRONTEND_PIDS"
    kill $FRONTEND_PIDS 2>/dev/null
    sleep 1
    # Force kill if still running
    if pgrep -f "next dev" > /dev/null; then
        echo "Force stopping frontend..."
        pkill -9 -f "next dev"
    fi
    echo -e "${GREEN}✓ Frontend stopped${NC}"
else
    echo -e "${YELLOW}No frontend process found${NC}"
fi

echo ""
echo "======================================"
echo -e "${GREEN}HA Discover stopped${NC}"
echo "======================================"
echo ""

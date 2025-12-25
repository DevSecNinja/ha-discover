#!/bin/bash
set -e

# Entrypoint script for hadiscover backend container
# Supports running as a web server or as a one-time indexing job

if [ "$1" = "index-once" ]; then
    echo "Running indexing job..."
    exec python -m app.cli index-once
else
    echo "Starting web server..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
fi

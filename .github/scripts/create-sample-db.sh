#!/bin/bash
# Create a sample SQLite database from the hadiscover models for schema diagram generation

set -e

echo "Creating sample database from models..."

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Install backend dependencies using the shared script
echo "Installing backend dependencies..."
cd "$PROJECT_ROOT"
.github/scripts/install-backend-deps.sh

# Create a temporary Python script to generate the database
cat > /tmp/create_db.py << 'EOF'
"""Generate sample SQLite database from SQLAlchemy models."""
from app.models.database import Base
from sqlalchemy import create_engine

# Create engine and database
engine = create_engine('sqlite:///sample_schema.db')
Base.metadata.create_all(engine)

print("Sample database created successfully at backend/sample_schema.db")
EOF

# Set PYTHONPATH and run the script
cd "$BACKEND_DIR"
export PYTHONPATH="$BACKEND_DIR:$PYTHONPATH"
python /tmp/create_db.py

# Clean up
rm /tmp/create_db.py

echo "Database creation complete."

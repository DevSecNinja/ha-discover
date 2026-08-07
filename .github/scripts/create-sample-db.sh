#!/bin/bash
# Create a sample SQLite database with the hadiscover schema
# Usage: create-sample-db.sh <output-path>
# The database file is created using the SQLAlchemy models from the backend.

set -e

OUTPUT_PATH="${1:?Usage: create-sample-db.sh <output-path>}"

echo "Creating sample database at ${OUTPUT_PATH}..."

DATABASE_URL="sqlite:///${OUTPUT_PATH}" python -c "
from app.models.database import Base
from sqlalchemy import create_engine
import os

engine = create_engine(os.environ['DATABASE_URL'])
Base.metadata.create_all(bind=engine)
engine.dispose()
"

echo "✓ Sample database created at ${OUTPUT_PATH}"

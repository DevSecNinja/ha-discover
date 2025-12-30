#!/usr/bin/env python3
"""Database migration script to add line number columns."""

import sqlite3
import sys
from pathlib import Path


def migrate_database(db_path: str = "./data/hadiscover.db"):
    """Add start_line and end_line columns to automations table."""
    db_file = Path(db_path)

    if not db_file.exists():
        print(f"Database file not found: {db_path}")
        print("No migration needed - columns will be created on first run.")
        return True

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Check if columns already exist
            cursor.execute("PRAGMA table_info(automations)")
            columns = [row[1] for row in cursor.fetchall()]

            migrations_needed = []
            if "start_line" not in columns:
                migrations_needed.append("start_line")
            if "end_line" not in columns:
                migrations_needed.append("end_line")

            if not migrations_needed:
                print("✓ Database already has line number columns")
                return True

            print(f"Adding columns: {', '.join(migrations_needed)}")

            # Add columns
            if "start_line" not in columns:
                cursor.execute("ALTER TABLE automations ADD COLUMN start_line INTEGER")
                print("✓ Added start_line column")

            if "end_line" not in columns:
                cursor.execute("ALTER TABLE automations ADD COLUMN end_line INTEGER")
                print("✓ Added end_line column")

            conn.commit()

        print("✓ Database migration completed successfully")
        return True
    except Exception as e:
        print(f"✗ Migration failed: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "./data/hadiscover.db"
    success = migrate_database(db_path)
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
migrate_phase8.py

Phase 8.5 migration — additive only, safe to re-run:
  1. Creates the memory_photo table (db.create_all).
  2. Adds journal_entry.location column if missing (ALTER TABLE).

Usage (from project root):
    python migrate_phase8.py
"""

from sqlalchemy import inspect, text

from app import create_app
from app.extensions import db


def migrate():
    app = create_app()
    with app.app_context():
        db.create_all()
        print("create_all OK (memory_photo table ensured)")

        inspector = inspect(db.engine)
        columns = [c["name"] for c in inspector.get_columns("journal_entry")]
        if "location" not in columns:
            db.session.execute(
                text("ALTER TABLE journal_entry ADD COLUMN location VARCHAR(200)")
            )
            db.session.commit()
            print("Added journal_entry.location column")
        else:
            print("journal_entry.location already present — skipped")

        print("Migration complete.")


if __name__ == "__main__":
    migrate()

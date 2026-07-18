"""KRONOS_DATA_HUB - Database Migrations"""
import os
import json
from datetime import datetime
from typing import List, Dict, Optional

class MigrationManager:
    MIGRATION_TABLE = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    def __init__(self, db_manager):
        self.db = db_manager
        self._ensure_migration_table()

    def _ensure_migration_table(self):
        self.db.execute(self.MIGRATION_TABLE)

    def get_applied_migrations(self):
        rows = self.db.fetch_all("SELECT version FROM schema_migrations ORDER BY version")
        return [r["version"] for r in rows]

    def is_applied(self, version):
        result = self.db.fetch_one("SELECT 1 FROM schema_migrations WHERE version = ?", (version,))
        return result is not None

    def apply_migration(self, version, name, sql):
        if self.is_applied(version):
            return False
        self.db.execute(sql)
        self.db.execute("INSERT INTO schema_migrations (version, name) VALUES (?, ?)", (version, name))
        return True

    def get_status(self):
        applied = self.get_applied_migrations()
        return {
            "applied_count": len(applied),
            "last_applied": applied[-1] if applied else None,
            "applied_versions": applied
        }

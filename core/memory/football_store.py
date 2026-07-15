"""
core/memory/football_store.py

Zamanlayıcının çektiği fütbol lig tablolarının (puan durumu) en güncel
halini SQLite'a kaydeder. Böylece hem anlık sorular hem de ileride
eklenecek analiz/rapor özellikleri aynı veriyi kullanabilir.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path("/tmp/kronos_football.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS standings (
            league_key TEXT PRIMARY KEY,
            league_name TEXT NOT NULL,
            payload TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    return conn


def save_standings(league_key: str, league_name: str, table_data: list[dict[str, Any]]) -> None:
    conn = _get_conn()
    conn.execute(
        """
        INSERT INTO standings (league_key, league_name, payload, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(league_key) DO UPDATE SET
            payload = excluded.payload,
            updated_at = excluded.updated_at
        """,
        (
            league_key,
            league_name,
            json.dumps(table_data, ensure_ascii=False),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()


def load_standings(league_key: str) -> Optional[dict[str, Any]]:
    conn = _get_conn()
    cur = conn.execute(
        "SELECT league_name, payload, updated_at FROM standings WHERE league_key = ?",
        (league_key,),
    )
    row = cur.fetchone()
    if not row:
        return None
    league_name, payload, updated_at = row
    return {
        "league_name": league_name,
        "table": json.loads(payload),
        "updated_at": updated_at,
    }


def list_tracked_leagues() -> list[str]:
    conn = _get_conn()
    cur = conn.execute("SELECT league_key FROM standings")
    return [row[0] for row in cur.fetchall()]

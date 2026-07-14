"""
core/memory/persistent.py

ShortTermMemory ile aynı arayüzü (add_user_message, add_assistant_message,
add_raw, get_messages, clear) sunar ama mesajları SQLite'a yazar. Böylece
sunucu her /chat isteğinde hafızayı sıfırdan başlatmak yerine, aynı
session_id ile gelen istekler için konuşmanın devamını hatırlar.

Not: Render'ın ücretsiz planında disk kalıcı değildir — servis yeniden
deploy edilirse (kod güncellemesi vs.) veritabanı sıfırlanır. Ama servis
ayakta kaldığı sürece (birden fazla istek arasında) hafıza korunur.
"""

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DB_PATH = Path("/tmp/kronos_memory.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return conn


@dataclass
class PersistentMemory:
    """Tek bir session_id'ye ait mesaj geçmişini SQLite'ta tutar."""

    session_id: str
    max_messages: int = 40

    def __post_init__(self) -> None:
        self._conn = _get_conn()

    def add_user_message(self, content: str) -> None:
        self._append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        self._append({"role": "assistant", "content": content})

    def add_raw(self, message: dict[str, Any]) -> None:
        self._append(message)

    def _append(self, message: dict[str, Any]) -> None:
        self._conn.execute(
            "INSERT INTO messages (session_id, payload) VALUES (?, ?)",
            (self.session_id, json.dumps(message)),
        )
        self._conn.commit()
        self._trim()

    def get_messages(self) -> list[dict[str, Any]]:
        cur = self._conn.execute(
            "SELECT payload FROM messages WHERE session_id = ? ORDER BY id ASC",
            (self.session_id,),
        )
        return [json.loads(row[0]) for row in cur.fetchall()]

    def clear(self) -> None:
        self._conn.execute("DELETE FROM messages WHERE session_id = ?", (self.session_id,))
        self._conn.commit()

    def _trim(self) -> None:
        cur = self._conn.execute(
            "SELECT COUNT(*) FROM messages WHERE session_id = ?", (self.session_id,)
        )
        count = cur.fetchone()[0]
        if count > self.max_messages:
            overflow = count - self.max_messages
            self._conn.execute(
                """
                DELETE FROM messages WHERE id IN (
                    SELECT id FROM messages WHERE session_id = ?
                    ORDER BY id ASC LIMIT ?
                )
                """,
                (self.session_id, overflow),
            )
            self._conn.commit()

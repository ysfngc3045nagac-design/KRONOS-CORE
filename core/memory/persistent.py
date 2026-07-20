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
            "SELECT id, payload FROM messages WHERE session_id = ? ORDER BY id ASC",
            (self.session_id,),
        )
        rows = cur.fetchall()
        if len(rows) <= self.max_messages:
            return
        overflow = len(rows) - self.max_messages
        # DUZELTME: eskiden satirlar id sirasina gore tek tek siliniyordu.
        # Bu, bir assistant "tool_use" satiriyla onu izleyen "tool_result"
        # satirini ortadan bolebiliyordu - sonuc, saglayiciya (ozellikle
        # OpenAI uyumlu Groq/Mistral, "tool" rolundeki mesajin karsiligi
        # olan tool_calls'u bulamayinca hata veriyor) bozuk/eslesmeyen bir
        # baglam gonderiliyordu ve sohbet o session'da calismaz hale
        # gelebiliyordu. Simdi kesim noktasi, bir tool_use+tool_result
        # ciftini asla bolmeyecek sekilde ayarlaniyor.
        cutoff = overflow
        if 0 < cutoff < len(rows):
            def _has_block_type(payload_json: str, block_type: str) -> bool:
                payload = json.loads(payload_json)
                content = payload.get("content")
                return isinstance(content, list) and any(
                    isinstance(b, dict) and b.get("type") == block_type for b in content
                )

            if _has_block_type(rows[cutoff - 1][1], "tool_use") and _has_block_type(
                rows[cutoff][1], "tool_result"
            ):
                cutoff += 1  # cifti birlikte sil, yariya bolme

        ids_to_delete = [row[0] for row in rows[:cutoff]]
        if ids_to_delete:
            self._conn.executemany(
                "DELETE FROM messages WHERE id = ?", [(i,) for i in ids_to_delete]
            )
            self._conn.commit()

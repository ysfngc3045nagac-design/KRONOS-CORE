"""
core/memory/short_term.py

Faz 1'de hafıza katmanının sadece "kısa vadeli" kısmı var: aktif
konuşmanın mesaj geçmişi. medium_term.py (oturum hafızası) ve
long_term.py (bilgi grafiği + vektör arama) ileride, gerçekten
ihtiyaç doğduğunda eklenecek — şimdiden inşa etmek erken optimizasyon
olur.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ShortTermMemory:
    """Tek bir konuşmanın mesaj geçmişini tutar ve token bütçesini yönetir."""

    max_messages: int = 40  # basit bir üst sınır; taşınca en eski mesajlar atılır
    messages: list[dict[str, Any]] = field(default_factory=list)

    def add_user_message(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})
        self._trim()

    def add_assistant_message(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})
        self._trim()

    def add_raw(self, message: dict[str, Any]) -> None:
        """Tool-use gibi karmaşık mesaj bloklarını olduğu gibi eklemek için."""
        self.messages.append(message)
        self._trim()

    def get_messages(self) -> list[dict[str, Any]]:
        return list(self.messages)

    def clear(self) -> None:
        self.messages.clear()

    def _trim(self) -> None:
        if len(self.messages) > self.max_messages:
            overflow = len(self.messages) - self.max_messages
            self.messages = self.messages[overflow:]

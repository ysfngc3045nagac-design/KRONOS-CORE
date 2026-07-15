"""Kullanici oturumu."""

from dataclasses import dataclass, field


@dataclass
class Session:
    session_id: str
    user_id: str | None = None
    metadata: dict = field(default_factory=dict)

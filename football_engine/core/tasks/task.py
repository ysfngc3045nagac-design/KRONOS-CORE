"""
Calistirilabilir Task arayuzu.

NOT: Ayni isimde iki Task tanimi vardi - biri dataclass (id/name/payload/
status alanlariyla, execute() metodu yok), digeri ABC (sadece execute()
soyut metodu). Ikisi birbiriyle uyumsuzdu. Bu versiyon ikisini birlestiriyor:
somut alanlari OLAN ama execute()'u da olan tek bir taban sinif.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TaskRecord:
    """Bir gorevin durumunu/gecmisini tutan veri (eski dataclass-Task'in yerine gecti)."""

    id: str
    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    status: str = "waiting"
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None


class Task(ABC):
    """Calistirilabilir gorev govdesi."""

    @abstractmethod
    def execute(self):
        ...

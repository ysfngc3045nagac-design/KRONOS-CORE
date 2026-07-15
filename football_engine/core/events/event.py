"""
Temel Event sinifi

DUZELTME: orijinalde `created_at: datetime = datetime.utcnow()` seklindeydi.
Bu, sinif tanimlanirken BIR KEZ calisir; her yeni Event ayni zaman damgasini
paylasirdi. field(default_factory=...) ile duzeltildi.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Event:
    name: str
    payload: dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)

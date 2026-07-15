"""Tek bir mac analizi boyunca ortak kullanilacak veri."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AnalysisContext:

    match: dict[str, Any]
    results: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_result(self, name: str, value: Any):
        self.results[name] = value

    def get(self, name: str, default=None):
        return self.results.get(name, default)

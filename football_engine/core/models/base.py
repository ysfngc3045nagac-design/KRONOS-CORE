"""
Tum model adaptorlerinin uyacagi ortak arayuz.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ModelCapabilities:
    supports_tools: bool = False
    supports_images: bool = False
    supports_streaming: bool = False
    supports_system_prompt: bool = True
    max_context_tokens: Optional[int] = None


class BaseModelAdapter(ABC):

    @abstractmethod
    def name(self) -> str:
        """Adaptorun adini dondurur (Kernel.health() bunu kullanir)."""
        ...

    @abstractmethod
    def complete(self, messages: list[dict], system: str = "", tools: list[dict] | None = None) -> dict:
        """
        Standart bir tamamlama cagrisi yapar.
        Donus: {"text": str, "tool_calls": list[dict], "raw": Any}
        """
        ...

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities()

    def health(self) -> bool:
        return True

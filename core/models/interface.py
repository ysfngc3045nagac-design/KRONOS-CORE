"""
core/models/interface.py

Model-agnostik arayüz. Kronos'un "beyni" hangi AI sağlayıcısını kullanırsa
kullansın, aynı şekilde konuşabilmeli. Yeni bir model eklemek istediğinde
(OpenAI, yerel model, vs.) sadece bu arayüzü uygulayan yeni bir adaptör
yazman yeterli — dispatcher.py ve geri kalan hiçbir şeyi değiştirmen gerekmez.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolCall:
    """Modelin çağırmak istediği bir aracın adı ve parametreleri."""
    name: str
    arguments: dict[str, Any]
    call_id: str


@dataclass
class ModelResponse:
    """Bir modelin tek bir isteğe verdiği standart yanıt."""
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: Any = None  # Sağlayıcıya özel ham yanıt (debug için saklanır)
    usage: Optional[dict[str, int]] = None  # örn. {"input_tokens": 120, "output_tokens": 45}


class ModelAdapter(ABC):
    """
    Her AI sağlayıcı adaptörü bu sınıfı miras almalı.
    Amaç: dispatcher.py hiçbir zaman "Anthropic mi, OpenAI mi" diye
    sormasın; sadece bu üç metodu çağırsın.
    """

    @abstractmethod
    def complete(
        self,
        messages: list[dict[str, Any]],
        system: str = "",
        tools: Optional[list[dict[str, Any]]] = None,
        max_tokens: int = 1024,
    ) -> ModelResponse:
        """Modelden tek seferlik bir yanıt al (streaming yok, basit versiyon)."""
        raise NotImplementedError

    @abstractmethod
    def name(self) -> str:
        """Adaptörün kimliği, örn. 'anthropic:claude-sonnet-4-6'."""
        raise NotImplementedError

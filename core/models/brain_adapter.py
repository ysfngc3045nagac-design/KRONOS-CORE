"""
core/models/brain_adapter.py

Kronos'un "beyni": birden fazla model sağlayıcısını sırayla dener.
Biri hata verirse (kota doldu, bağlantı sorunu, geçici kesinti vb.)
otomatik olarak bir sonrakine geçer - kullanıcı hiçbir şey fark etmez.

Sıra önemlidir: en hızlı/en güvenilir olan en başta olmalı.
"""

from typing import Any, Optional

from core.models.interface import ModelAdapter, ModelResponse


class BrainAdapter(ModelAdapter):
    def __init__(self, adapters: list[ModelAdapter]):
        if not adapters:
            raise RuntimeError(
                "BrainAdapter için en az bir model adaptörü gerekiyor "
                "(hiçbir API anahtarı bulunamadı)."
            )
        self.adapters = adapters
        self.last_used: Optional[str] = None

    def name(self) -> str:
        chain = " → ".join(a.name() for a in self.adapters)
        used = f" (son kullanılan: {self.last_used})" if self.last_used else ""
        return f"brain[{chain}]{used}"

    def complete(
        self,
        messages: list[dict[str, Any]],
        system: str = "",
        tools: Optional[list[dict[str, Any]]] = None,
        max_tokens: int = 1024,
    ) -> ModelResponse:
        last_error: Optional[Exception] = None

        for adapter in self.adapters:
            try:
                response = adapter.complete(
                    messages=messages, system=system, tools=tools, max_tokens=max_tokens
                )
                self.last_used = adapter.name()
                return response
            except Exception as exc:
                print(f"[Kronos Beyin] {adapter.name()} başarısız oldu: {exc}")
                last_error = exc
                continue

        # Hepsi başarısız oldu - çökmek yerine kullanıcıya nazik bir mesaj ver.
        return ModelResponse(
            text=(
                "Şu anda hiçbir model sağlayıcısına ulaşamadım "
                f"(son hata: {last_error}). Birkaç dakika sonra tekrar dener misin?"
            ),
            tool_calls=[],
            raw=None,
            usage=None,
        )

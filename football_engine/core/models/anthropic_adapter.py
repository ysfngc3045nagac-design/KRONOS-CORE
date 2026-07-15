"""
Anthropic (Claude) model adaptoru.

NOT: Bu dosya daha once hic paylasilmamisti, MasterController/ModelSelector
onu import ediyordu ama kodu yoktu. Calisir bir minimal implementasyon
yazildi. ANTHROPIC_API_KEY ortam degiskeni gerektirir.
"""

import os
from football_engine.core.models.base import BaseModelAdapter, ModelCapabilities


class AnthropicAdapter(BaseModelAdapter):

    def __init__(self, model: str = "claude-sonnet-4-6"):
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError as exc:
                raise RuntimeError(
                    "anthropic paketi kurulu degil. `pip install anthropic --break-system-packages`"
                ) from exc

            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise RuntimeError("ANTHROPIC_API_KEY ortam degiskeni tanimli degil.")

            self._client = anthropic.Anthropic(api_key=api_key)

        return self._client

    def name(self) -> str:
        return f"anthropic:{self.model}"

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            supports_tools=True,
            supports_images=True,
            supports_streaming=True,
            supports_system_prompt=True,
            max_context_tokens=200_000,
        )

    def health(self) -> bool:
        return bool(os.getenv("ANTHROPIC_API_KEY"))

    def complete(self, messages: list[dict], system: str = "", tools: list[dict] | None = None) -> dict:

        client = self._get_client()

        kwargs = {
            "model": self.model,
            "max_tokens": 2048,
            "messages": messages,
        }

        if system:
            kwargs["system"] = system

        if tools:
            kwargs["tools"] = tools

        response = client.messages.create(**kwargs)

        text_parts = []
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })

        return {
            "text": "\n".join(text_parts),
            "tool_calls": tool_calls,
            "raw": response,
        }

"""
core/models/anthropic_adapter.py

interface.py'deki ModelAdapter sözleşmesinin Claude (Anthropic API) ile
dolduruluşu. Faz 1'de tek adaptör bu — ileride openai_adapter.py veya
local_adapter.py eklemek istersen aynı ModelAdapter'ı miras alman yeterli.

Ortam değişkeni gerekli: ANTHROPIC_API_KEY
(Render'da: Environment > Add Environment Variable)
"""

import os
from typing import Any, Optional

import anthropic

from core.models.interface import ModelAdapter, ModelResponse, ToolCall


class AnthropicAdapter(ModelAdapter):
    def __init__(self, model: str = "claude-sonnet-4-6", api_key: Optional[str] = None):
        self.model = model
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY bulunamadı. Render ortam değişkenlerine eklemen gerekiyor."
            )
        self.client = anthropic.Anthropic(api_key=key)

    def name(self) -> str:
        return f"anthropic:{self.model}"

    def complete(
        self,
        messages: list[dict[str, Any]],
        system: str = "",
        tools: Optional[list[dict[str, Any]]] = None,
        max_tokens: int = 1024,
    ) -> ModelResponse:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools

        response = self.client.messages.create(**kwargs)

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(name=block.name, arguments=block.input, call_id=block.id)
                )

        return ModelResponse(
            text="".join(text_parts),
            tool_calls=tool_calls,
            raw=response,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        )

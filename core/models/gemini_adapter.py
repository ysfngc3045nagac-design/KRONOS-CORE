"""
core/models/gemini_adapter.py

interface.py'deki ModelAdapter sözleşmesinin Google Gemini API ile
dolduruluşu. Kredi kartı gerektirmeyen ücretsiz kotaya sahip bir
sağlayıcı olarak eklendi.

Ortam değişkeni gerekli: GEMINI_API_KEY
(Render'da: Environment > Add Environment Variable)
"""

import os
from typing import Any, Optional

import google.generativeai as genai

from core.models.interface import ModelAdapter, ModelResponse, ToolCall


class GeminiAdapter(ModelAdapter):
    def __init__(self, model: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        self.model_name = model
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise RuntimeError(
                "GEMINI_API_KEY bulunamadı. Render ortam değişkenlerine eklemen gerekiyor."
            )
        genai.configure(api_key=key)
        self.client = genai.GenerativeModel(self.model_name)

    def name(self) -> str:
        return f"gemini:{self.model_name}"

    def _to_gemini_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Anthropic tarzı {role, content} mesajlarını Gemini formatına çevirir."""
        converted = []
        for msg in messages:
            role = "model" if msg.get("role") == "assistant" else "user"
            content = msg.get("content", "")

            if isinstance(content, str):
                text = content
            else:
                # Anthropic tarzı blok listesi geldiyse (tool_use/tool_result vs.)
                # sadece metin bloklarını al; Faz 1'de araçsız kullanım için yeterli.
                text_parts = [
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                ]
                text = "".join(text_parts)

            if text:
                converted.append({"role": role, "parts": [text]})

        return converted

    def complete(
        self,
        messages: list[dict[str, Any]],
        system: str = "",
        tools: Optional[list[dict[str, Any]]] = None,
        max_tokens: int = 1024,
    ) -> ModelResponse:
        gemini_messages = self._to_gemini_messages(messages)

        model = self.client
        if system:
            model = genai.GenerativeModel(self.model_name, system_instruction=system)

        response = model.generate_content(
            gemini_messages,
            generation_config={"max_output_tokens": max_tokens},
        )

        text = response.text if response.candidates else ""

        usage = None
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = {
                "input_tokens": response.usage_metadata.prompt_token_count,
                "output_tokens": response.usage_metadata.candidates_token_count,
            }

        # Not: Gemini'nin fonksiyon çağırma (tool use) formatı Anthropic'ten
        # farklıdır. Faz 1'de tool_calls desteklenmiyor; ileride ihtiyaç
        # olursa response.candidates[0].content.parts içindeki
        # function_call bloklarından ToolCall listesi üretilebilir.
        return ModelResponse(
            text=text,
            tool_calls=[],
            raw=response,
            usage=usage,
        )

"""
Google Gemini model adaptoru.

NOT: Bu dosya daha once hic paylasilmamisti, ModelSelector onu import
ediyordu ama kodu yoktu. Calisir bir minimal implementasyon yazildi.
GEMINI_API_KEY ortam degiskeni gerektirir.
"""

import os
from football_engine.core.models.base import BaseModelAdapter, ModelCapabilities


class GeminiAdapter(BaseModelAdapter):

    def __init__(self, model: str = "gemini-2.0-flash"):
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import google.generativeai as genai
            except ImportError as exc:
                raise RuntimeError(
                    "google-generativeai paketi kurulu degil. "
                    "`pip install google-generativeai --break-system-packages`"
                ) from exc

            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise RuntimeError("GEMINI_API_KEY ortam degiskeni tanimli degil.")

            genai.configure(api_key=api_key)
            self._client = genai.GenerativeModel(self.model)

        return self._client

    def name(self) -> str:
        return f"gemini:{self.model}"

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            supports_tools=True,
            supports_images=True,
            supports_streaming=True,
            supports_system_prompt=True,
            max_context_tokens=1_000_000,
        )

    def health(self) -> bool:
        return bool(os.getenv("GEMINI_API_KEY"))

    def complete(self, messages: list[dict], system: str = "", tools: list[dict] | None = None) -> dict:

        client = self._get_client()

        prompt = "\n".join(m.get("content", "") for m in messages if isinstance(m.get("content"), str))

        if system:
            prompt = f"{system}\n\n{prompt}"

        response = client.generate_content(prompt)

        return {
            "text": response.text if hasattr(response, "text") else "",
            "tool_calls": [],
            "raw": response,
        }

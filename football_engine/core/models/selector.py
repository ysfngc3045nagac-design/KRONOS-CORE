"""Model secici"""

import os

from football_engine.core.models.gemini_adapter import GeminiAdapter
from football_engine.core.models.anthropic_adapter import AnthropicAdapter


class ModelSelector:

    def __init__(self):
        self.provider = os.getenv("MODEL_PROVIDER", "anthropic").lower()

    def build(self):

        if self.provider == "anthropic":
            return AnthropicAdapter()

        if self.provider == "gemini":
            return GeminiAdapter()

        raise RuntimeError(f"Desteklenmeyen model: {self.provider}")

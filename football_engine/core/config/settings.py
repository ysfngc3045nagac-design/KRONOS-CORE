"""
KRONOS merkezi ayarlar (birlestirilmis, tek kaynak)
"""

import os


class Settings:

    APP_NAME = "KRONOS"
    VERSION = "1.0.0"

    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "anthropic")

    MAX_MEMORY_MESSAGES = int(os.getenv("MAX_MEMORY_MESSAGES", "40"))
    MAX_TOOL_ITERATIONS = int(os.getenv("MAX_TOOL_ITERATIONS", "5"))

    REPORT_DIRECTORY = os.getenv("REPORT_DIRECTORY", "reports")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "/tmp/kronos_memory.db")

    ANALYSIS_CRITERIA = 50
    CACHE_TTL = 3600

    DEFAULT_LANGUAGE = "tr"

    @property
    def anthropic_key(self):
        return os.getenv("ANTHROPIC_API_KEY")

    @property
    def gemini_key(self):
        return os.getenv("GEMINI_API_KEY")


settings = Settings()

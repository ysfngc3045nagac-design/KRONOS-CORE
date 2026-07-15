"""Metin isleme araclari"""

import re
from football_engine.core.tools.registry import tool_registry


@tool_registry.register(
    name="word_count",
    description="Metindeki kelime sayisini hesaplar.",
    parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
)
def word_count(text: str) -> dict:
    return {"words": len(text.split())}


@tool_registry.register(
    name="character_count",
    description="Metindeki karakter sayisini hesaplar.",
    parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
)
def character_count(text: str) -> dict:
    return {"characters": len(text)}


@tool_registry.register(
    name="uppercase",
    description="Metni buyuk harfe cevirir.",
    parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
)
def uppercase(text: str) -> str:
    return text.upper()


@tool_registry.register(
    name="lowercase",
    description="Metni kucuk harfe cevirir.",
    parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
)
def lowercase(text: str) -> str:
    return text.lower()


@tool_registry.register(
    name="regex_search",
    description="Regex ile metin icinde arama yapar.",
    parameters={
        "type": "object",
        "properties": {"pattern": {"type": "string"}, "text": {"type": "string"}},
        "required": ["pattern", "text"],
    },
)
def regex_search(pattern: str, text: str):
    return re.findall(pattern, text)

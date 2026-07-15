"""
HTTP araclari

DUZELTME: orijinalde cache'li http_get parcasi (cache_key = f"GET:{url}"...)
fonksiyon govdesinin disinda, tamamlanmamis bir fragman olarak gelmisti.
Tek, tamamlanmis ve cache'li bir http_get fonksiyonunda birlestirildi.
"""

from typing import Any
import requests

from football_engine.core.tools.registry import tool_registry
from football_engine.core.tools.cache import _cache

DEFAULT_HEADERS = {"User-Agent": "KRONOS/1.0"}


@tool_registry.register(
    name="http_get", description="Bir HTTP GET istegi yapar (300sn cache'li).",
    parameters={
        "type": "object",
        "properties": {"url": {"type": "string"}, "timeout": {"type": "integer"}},
        "required": ["url"],
    },
)
def http_get(url: str, timeout: int = 15) -> Any:

    cache_key = f"GET:{url}"
    cached = _cache.get(cache_key)

    if cached is not None:
        return cached

    response = requests.get(url, timeout=timeout, headers=DEFAULT_HEADERS)
    response.raise_for_status()

    try:
        result = response.json()
    except Exception:
        result = response.text

    _cache.set(cache_key, result, ttl=300)

    return result


@tool_registry.register(
    name="http_post", description="JSON govdesi ile HTTP POST istegi yapar.",
    parameters={
        "type": "object",
        "properties": {"url": {"type": "string"}, "data": {"type": "object"}},
        "required": ["url", "data"],
    },
)
def http_post(url: str, data: dict):
    response = requests.post(url, json=data, timeout=20, headers=DEFAULT_HEADERS)
    response.raise_for_status()
    try:
        return response.json()
    except Exception:
        return response.text


@tool_registry.register(
    name="cache_clear", description="HTTP onbellegini temizler.",
    parameters={"type": "object", "properties": {}, "required": []},
)
def cache_clear():
    _cache.clear()
    return "OK"

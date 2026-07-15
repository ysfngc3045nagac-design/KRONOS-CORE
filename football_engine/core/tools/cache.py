"""Basit bellek ici onbellek (tools icin paylasilan tek kaynak)"""

import time
from typing import Any


class Cache:

    def __init__(self):
        self._items = {}

    def set(self, key: str, value: Any, ttl: int = 300):
        self._items[key] = {"value": value, "expire": time.time() + ttl}

    def get(self, key: str):
        item = self._items.get(key)
        if item is None:
            return None
        if time.time() > item["expire"]:
            del self._items[key]
            return None
        return item["value"]

    def delete(self, key: str):
        self._items.pop(key, None)

    def clear(self):
        self._items.clear()


_cache = Cache()

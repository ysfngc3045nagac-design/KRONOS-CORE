"""KRONOS_DATA_HUB - Cache Manager"""
import json
import hashlib
import pickle
import time
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta
from collections import OrderedDict
from threading import Lock
from .sqlite_manager import SQLiteManager

class CacheManager:
    def __init__(self, db_manager, memory_size=1000, default_ttl_seconds=3600):
        self.db = db_manager
        self.memory_size = memory_size
        self.default_ttl = default_ttl_seconds
        self._memory_cache = OrderedDict()
        self._memory_lock = Lock()
        self._hits = 0
        self._misses = 0
        self._memory_hits = 0
        self._disk_hits = 0

    def _generate_key(self, prefix, identifier):
        key_str = f"{prefix}:{json.dumps(identifier, sort_keys=True, default=str)}"
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, prefix, identifier, default=None):
        key = self._generate_key(prefix, identifier)
        with self._memory_lock:
            if key in self._memory_cache:
                self._memory_cache.move_to_end(key)
                self._hits += 1
                self._memory_hits += 1
                return self._memory_cache[key]
        result = self.db.fetch_one(
            "SELECT value, expires_at FROM cache_entries WHERE key = ?", (key,))
        if result:
            expires_at = datetime.fromisoformat(result['expires_at'])
            if datetime.now() < expires_at:
                value = pickle.loads(result['value'].encode('latin1'))
                self._put_memory(key, value)
                self._hits += 1
                self._disk_hits += 1
                return value
            else:
                self.db.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
        self._misses += 1
        return default

    def set(self, prefix, identifier, value, ttl_seconds=None):
        key = self._generate_key(prefix, identifier)
        ttl = ttl_seconds or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        self._put_memory(key, value)
        try:
            serialized = pickle.dumps(value).decode('latin1')
            self.db.execute(
                "INSERT OR REPLACE INTO cache_entries (key, value, expires_at) VALUES (?, ?, ?)",
                (key, serialized, expires_at.isoformat()))
        except Exception:
            pass

    def _put_memory(self, key, value):
        with self._memory_lock:
            if key in self._memory_cache:
                self._memory_cache.move_to_end(key)
            else:
                if len(self._memory_cache) >= self.memory_size:
                    self._memory_cache.popitem(last=False)
                self._memory_cache[key] = value

    def delete(self, prefix, identifier):
        key = self._generate_key(prefix, identifier)
        with self._memory_lock:
            self._memory_cache.pop(key, None)
        self.db.execute("DELETE FROM cache_entries WHERE key = ?", (key,))

    def clear(self, prefix=None):
        with self._memory_lock:
            if prefix:
                keys_to_remove = [k for k in self._memory_cache.keys() if k.startswith(prefix)]
                for k in keys_to_remove:
                    del self._memory_cache[k]
                self.db.execute("DELETE FROM cache_entries WHERE key LIKE ?", (f"{prefix}%",))
            else:
                self._memory_cache.clear()
                self.db.execute("DELETE FROM cache_entries")

    def invalidate_expired(self):
        now = datetime.now().isoformat()
        result = self.db.execute("DELETE FROM cache_entries WHERE expires_at < ?", (now,))
        return result.rowcount

    def get_stats(self):
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        disk_count = self.db.fetch_scalar("SELECT COUNT(*) FROM cache_entries") or 0
        return {
            "memory_entries": len(self._memory_cache), "disk_entries": disk_count,
            "total_hits": self._hits, "memory_hits": self._memory_hits,
            "disk_hits": self._disk_hits, "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 2), "memory_size_limit": self.memory_size,
            "default_ttl_seconds": self.default_ttl
        }

    def get_cache_key_pattern(self, prefix, pattern):
        return self.db.fetch_all("SELECT key FROM cache_entries WHERE key LIKE ?", (f"{prefix}:{pattern}%",))

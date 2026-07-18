"""KRONOS_DATA_HUB - Rate Limiter"""
import time
import threading
from typing import Dict, Optional
from dataclasses import dataclass, field

@dataclass
class RateLimitConfig:
    requests_per_minute: int = 60
    burst_size: int = 10
    retry_after_seconds: float = 1.0
    def __post_init__(self):
        self.tokens_per_second = self.requests_per_minute / 60.0

class TokenBucket:
    def __init__(self, config):
        self.config = config
        self.tokens = config.burst_size
        self.last_update = time.monotonic()
        self._lock = threading.Lock()

    def _add_tokens(self):
        now = time.monotonic()
        elapsed = now - self.last_update
        tokens_to_add = elapsed * self.config.tokens_per_second
        self.tokens = min(self.config.burst_size, self.tokens + tokens_to_add)
        self.last_update = now

    def acquire(self, tokens=1, blocking=True, timeout=None):
        with self._lock:
            self._add_tokens()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            if not blocking:
                return False
            tokens_needed = tokens - self.tokens
            wait_time = tokens_needed / self.config.tokens_per_second
            if timeout is not None and wait_time > timeout:
                return False
        time.sleep(wait_time)
        with self._lock:
            self._add_tokens()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def try_acquire(self, tokens=1):
        with self._lock:
            self._add_tokens()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def get_status(self):
        with self._lock:
            self._add_tokens()
            return {
                "tokens": self.tokens, "max_tokens": self.config.burst_size,
                "tokens_per_second": self.config.tokens_per_second,
                "utilization_percent": round((1 - self.tokens / self.config.burst_size) * 100, 2)
            }

class RateLimiter:
    def __init__(self):
        self._buckets = {}
        self._configs = {}
        self._lock = threading.Lock()
        self._global_stats = {"total_requests": 0, "throttled_requests": 0, "start_time": time.monotonic()}

    def register_source(self, source_id, requests_per_minute=60, burst_size=10):
        config = RateLimitConfig(requests_per_minute=requests_per_minute, burst_size=burst_size)
        with self._lock:
            self._configs[source_id] = config
            self._buckets[source_id] = TokenBucket(config)

    def acquire(self, source_id, tokens=1, blocking=True, timeout=None):
        with self._lock:
            self._global_stats["total_requests"] += 1
            if source_id not in self._buckets:
                self.register_source(source_id)
            bucket = self._buckets[source_id]
        result = bucket.acquire(tokens, blocking, timeout)
        if not result:
            with self._lock:
                self._global_stats["throttled_requests"] += 1
        return result

    def try_acquire(self, source_id, tokens=1):
        return self.acquire(source_id, tokens, blocking=False)

    def wait_if_needed(self, source_id, tokens=1):
        start = time.monotonic()
        self.acquire(source_id, tokens, blocking=True)
        return time.monotonic() - start

    def get_source_status(self, source_id):
        with self._lock:
            if source_id not in self._buckets:
                return {"error": "Source not registered"}
            bucket_status = self._buckets[source_id].get_status()
            config = self._configs[source_id]
            return {"source_id": source_id, "requests_per_minute": config.requests_per_minute,
                    "burst_size": config.burst_size, **bucket_status}

    def get_all_status(self):
        with self._lock:
            return {source_id: self._buckets[source_id].get_status() for source_id in self._buckets}

    def get_global_stats(self):
        with self._lock:
            uptime = time.monotonic() - self._global_stats["start_time"]
            total = self._global_stats["total_requests"]
            throttled = self._global_stats["throttled_requests"]
            return {
                "total_requests": total, "throttled_requests": throttled,
                "throttle_rate_percent": round((throttled / total * 100) if total > 0 else 0, 2),
                "registered_sources": len(self._buckets), "uptime_seconds": round(uptime, 2)
            }

    def reset_source(self, source_id):
        with self._lock:
            if source_id in self._configs:
                self._buckets[source_id] = TokenBucket(self._configs[source_id])

    def adjust_limit(self, source_id, new_requests_per_minute):
        with self._lock:
            if source_id in self._configs:
                old_config = self._configs[source_id]
                new_config = RateLimitConfig(requests_per_minute=new_requests_per_minute, burst_size=old_config.burst_size)
                self._configs[source_id] = new_config
                self._buckets[source_id] = TokenBucket(new_config)

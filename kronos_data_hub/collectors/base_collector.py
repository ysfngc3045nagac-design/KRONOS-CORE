"""KRONOS_DATA_HUB - Base Collector"""
import json
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import requests
from core.rate_limiter import RateLimiter
from core.retry_manager import RetryManager, RetryConfig, CircuitBreakerConfig
from database.sqlite_manager import SQLiteManager
from database.cache import CacheManager
from parsers import JSONParser, XMLParser, CSVParser, HTMLParser, RSSParser

class BaseCollector(ABC):
    def __init__(self, source_id, config, db, rate_limiter, retry_manager, cache):
        self.source_id = source_id
        self.config = config
        self.db = db
        self.rate_limiter = rate_limiter
        self.retry_manager = retry_manager
        self.cache = cache
        self.logger = logging.getLogger(f"collector.{source_id}")
        self.json_parser = JSONParser()
        self.xml_parser = XMLParser()
        self.csv_parser = CSVParser()
        self.html_parser = HTMLParser()
        self.rss_parser = RSSParser()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": config.get("user_agent", "KRONOS_DATA_HUB/1.0"),
            "Accept": "application/json, text/html, */*", "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate", "Connection": "keep-alive"
        })
        self.stats = {"requests": 0, "successful": 0, "failed": 0, "cached": 0,
                      "records_collected": 0, "last_run": None, "total_time_ms": 0}

    def _build_url(self, endpoint_key, **kwargs):
        base = self.config.get("base_url", "").rstrip("/")
        endpoint = self.config.get("endpoints", {}).get(endpoint_key, "")
        try:
            endpoint = endpoint.format(**kwargs)
        except KeyError:
            pass
        return f"{base}{endpoint}"

    def _get_headers(self):
        headers = {}
        custom = self.config.get("headers", {})
        headers.update(custom)
        return headers

    def _make_request(self, url, method="GET", params=None, data=None, headers=None, timeout=None):
        timeout = timeout or self.config.get("timeout", 30)
        self.rate_limiter.wait_if_needed(self.source_id)
        req_headers = self._get_headers()
        if headers:
            req_headers.update(headers)
        start = time.time()
        def do_request():
            if method.upper() == "GET":
                return self.session.get(url, params=params, headers=req_headers, timeout=timeout)
            elif method.upper() == "POST":
                return self.session.post(url, json=data, headers=req_headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
        response = self.retry_manager.execute(self.source_id, do_request)
        elapsed_ms = (time.time() - start) * 1000
        self.stats["requests"] += 1
        self.stats["total_time_ms"] += elapsed_ms
        return response

    def _fetch_cached(self, cache_key, fetch_func, ttl=3600):
        cached = self.cache.get(self.source_id, cache_key)
        if cached is not None:
            self.stats["cached"] += 1
            return cached
        data = fetch_func()
        self.cache.set(self.source_id, cache_key, data, ttl)
        return data

    def _save_collection_log(self, operation, status, records=0, error="", duration_ms=0):
        self.db.execute(
            """INSERT INTO collection_logs (source_id, operation, status, records_count,
                error_message, duration_ms, started_at, completed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (self.source_id, operation, status, records, error, duration_ms,
             self.stats["last_run"], datetime.now().isoformat()))

    def _update_source_health(self, success, response_time_ms=0):
        now = datetime.now().isoformat()
        existing = self.db.fetch_one("SELECT * FROM source_health WHERE source_id = ?", (self.source_id,))
        if existing:
            if success:
                self.db.execute(
                    """UPDATE source_health SET status = 'healthy', last_check = ?, last_success = ?,
                       success_count = success_count + 1, avg_response_time_ms = (avg_response_time_ms + ?) / 2,
                       error_rate = failure_count * 1.0 / (success_count + failure_count + 1), updated_at = ?
                       WHERE source_id = ?""", (now, now, response_time_ms, now, self.source_id))
            else:
                self.db.execute(
                    """UPDATE source_health SET
                       status = CASE WHEN failure_count >= 4 THEN 'down' WHEN failure_count >= 2 THEN 'degraded' ELSE 'healthy' END,
                       last_check = ?, last_failure = ?, failure_count = failure_count + 1, updated_at = ?
                       WHERE source_id = ?""", (now, now, now, self.source_id))
        else:
            self.db.execute(
                """INSERT INTO source_health (source_id, status, last_check, last_success,
                    failure_count, success_count, avg_response_time_ms) VALUES (?, 'healthy', ?, ?, 0, 1, ?)""",
                (self.source_id, now, now, response_time_ms))

    @abstractmethod
    def collect(self, **kwargs):
        pass

    @abstractmethod
    def parse_response(self, response):
        pass

    def get_stats(self):
        return {"source_id": self.source_id, **self.stats,
                "avg_response_time_ms": round(self.stats["total_time_ms"] / max(self.stats["requests"], 1), 2)}

    def health_check(self):
        try:
            url = self._build_url("health", default="")
            if not url:
                return {"status": "unknown", "message": "No health endpoint"}
            start = time.time()
            response = self._make_request(url, timeout=10)
            elapsed = (time.time() - start) * 1000
            healthy = response.status_code < 400
            self._update_source_health(healthy, elapsed)
            return {"status": "healthy" if healthy else "unhealthy", "status_code": response.status_code,
                    "response_time_ms": round(elapsed, 2)}
        except Exception as e:
            self._update_source_health(False)
            return {"status": "down", "error": str(e), "response_time_ms": 0}

"""KRONOS_DATA_HUB - Source Manager"""
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from database.sqlite_manager import SQLiteManager
from database.cache import CacheManager
from core.rate_limiter import RateLimiter
from core.retry_manager import RetryManager, RetryConfig, CircuitBreakerConfig

class SourceManager:
    def __init__(self, config_path="config/sources.json", db=None, rate_limiter=None, retry_manager=None, cache=None):
        self.config_path = config_path
        self.db = db
        self.rate_limiter = rate_limiter or RateLimiter()
        self.retry_manager = retry_manager or RetryManager()
        self.cache = cache
        self.logger = logging.getLogger("source_manager")
        self.sources = {}
        self.collectors = {}
        self._load_config()
        self._register_sources()

    def _load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.sources = config.get("sources", {})
                self.global_settings = config.get("global_settings", {})
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            self.sources = {}
        self._load_api_keys()

    def _load_api_keys(self):
        """
        config/api_keys.json'i okuyup, requires_auth=true olan her kaynagin
        config sozlugune 'api_key' alanini enjekte eder. Onceki surumde bu
        dosya hic okunmuyordu; anahtarlar api_keys.json'a yazilsa bile
        collector'larin self.config.get('api_key') cagrisi hep bos donuyordu.

        Oncelik sirasi: 1) ortam degiskeni (os.getenv(API_KEY_REF.upper()))
        2) config/api_keys.json'daki deger. Ortam degiskeni varsa o kazanir
        (production/deploy ortamlarinda secrets genelde env ile verilir).
        """
        import os
        api_keys_path = os.path.join(os.path.dirname(self.config_path), "api_keys.json")
        stored_keys = {}
        try:
            with open(api_keys_path, "r", encoding="utf-8") as f:
                stored_keys = json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"api_keys.json bulunamadi: {api_keys_path}")
        except Exception as e:
            self.logger.error(f"api_keys.json okunamadi: {e}")

        for source_id, config in self.sources.items():
            if not config.get("requires_auth"):
                continue
            key_ref = config.get("api_key_ref", "")
            if not key_ref:
                continue
            env_value = os.getenv(key_ref.upper(), "")
            file_value = stored_keys.get(key_ref, "")
            resolved = env_value or file_value
            config["api_key"] = resolved
            if not resolved:
                self.logger.warning(f"'{source_id}' icin anahtar bulunamadi (beklenen: env {key_ref.upper()} veya api_keys.json['{key_ref}'])")

    def _register_sources(self):
        for source_id, config in self.sources.items():
            if not config.get("enabled", True):
                continue
            self.rate_limiter.register_source(source_id, requests_per_minute=config.get("rate_limit", 60),
                                               burst_size=min(config.get("rate_limit", 60), 20))
            self.retry_manager.register_source(source_id,
                retry_config=RetryConfig(max_retries=config.get("retry_count", 3), base_delay=1.0),
                breaker_config=CircuitBreakerConfig(failure_threshold=5, recovery_timeout=300))
            self.logger.info(f"Registered source: {source_id}")

    def get_source(self, source_id):
        return self.sources.get(source_id)

    def get_all_sources(self):
        return self.sources

    def get_enabled_sources(self):
        return {k: v for k, v in self.sources.items() if v.get("enabled", True)}

    def get_sources_by_type(self, data_type):
        return {k: v for k, v in self.sources.items() if data_type in v.get("data_types", [])}

    def get_sources_by_league(self, league):
        return {k: v for k, v in self.sources.items()
                if league in v.get("supported_leagues", []) or "all" in v.get("supported_leagues", [])}

    def register_collector(self, source_id, collector):
        self.collectors[source_id] = collector

    def get_collector(self, source_id):
        return self.collectors.get(source_id)

    def enable_source(self, source_id):
        if source_id in self.sources:
            self.sources[source_id]["enabled"] = True
            self._register_sources()
            return True
        return False

    def disable_source(self, source_id):
        if source_id in self.sources:
            self.sources[source_id]["enabled"] = False
            return True
        return False

    def get_source_health(self, source_id):
        if not self.db:
            return {"error": "No database connection"}
        health = self.db.fetch_one("SELECT * FROM source_health WHERE source_id = ?", (source_id,))
        if health:
            return dict(health)
        return {"status": "unknown", "source_id": source_id}

    def get_all_health(self):
        if not self.db:
            return []
        return self.db.fetch_all("SELECT * FROM source_health ORDER BY source_id")

    def get_stats(self):
        return {
            "total_sources": len(self.sources), "enabled_sources": len(self.get_enabled_sources()),
            "registered_collectors": len(self.collectors), "sources_by_priority": self._group_by_priority()
        }

    def _group_by_priority(self):
        groups = {}
        for source_id, config in self.sources.items():
            priority = config.get("priority", 5)
            level = "high" if priority >= 8 else "medium" if priority >= 5 else "low"
            groups.setdefault(level, []).append(source_id)
        return groups

    def reload_config(self):
        self._load_config()
        self._register_sources()
        self.logger.info("Configuration reloaded")

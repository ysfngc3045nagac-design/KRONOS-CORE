"""KRONOS_DATA_HUB - Source Validator"""
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

class SourceValidator:
    def __init__(self):
        self.validation_results = {}

    def validate_source(self, source_id, config):
        results = {"source_id": source_id, "timestamp": datetime.now().isoformat(), "checks": {}}
        results["checks"]["accessibility"] = self._check_accessibility(config)
        results["checks"]["structure"] = self._check_structure(config)
        if results["checks"]["accessibility"].get("status") == "ok":
            results["checks"]["data_quality"] = self._check_data_quality(config)
        results["checks"]["rate_limit"] = self._check_rate_limit(config)
        if config.get("requires_auth"):
            results["checks"]["authentication"] = self._check_authentication(config)
        passed = sum(1 for c in results["checks"].values() if c.get("status") == "ok")
        total = len(results["checks"])
        results["score"] = round(passed / total * 100, 2) if total > 0 else 0
        results["status"] = "valid" if results["score"] >= 80 else "invalid"
        self.validation_results[source_id] = results
        return results

    def _check_accessibility(self, config):
        base_url = config.get("base_url", "")
        try:
            response = requests.get(base_url, timeout=config.get("timeout", 10),
                                     headers={"User-Agent": config.get("user_agent", "KRONOS/1.0")})
            return {"status": "ok" if response.status_code < 500 else "error",
                    "status_code": response.status_code,
                    "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2), "url": base_url}
        except requests.exceptions.ConnectionError:
            return {"status": "error", "error": "Connection refused"}
        except requests.exceptions.Timeout:
            return {"status": "error", "error": "Request timeout"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _check_structure(self, config):
        checks = {
            "has_base_url": bool(config.get("base_url")), "has_endpoints": bool(config.get("endpoints")),
            "endpoints_valid": True, "has_rate_limit": "rate_limit" in config, "has_timeout": "timeout" in config
        }
        endpoints = config.get("endpoints", {})
        for name, url in endpoints.items():
            if "{" in url and "}" in url:
                pass
            elif not url.startswith("/"):
                checks["endpoints_valid"] = False
        all_ok = all(checks.values())
        return {"status": "ok" if all_ok else "warning", "checks": checks, "endpoint_count": len(endpoints)}

    def _check_data_quality(self, config):
        endpoints = config.get("endpoints", {})
        test_endpoint = None
        for key in ["fixtures", "matches", "events", "sports"]:
            if key in endpoints:
                test_endpoint = key
                break
        if not test_endpoint:
            return {"status": "warning", "message": "No testable endpoint found"}
        try:
            base = config["base_url"].rstrip("/")
            endpoint = endpoints[test_endpoint]
            test_url = f"{base}{endpoint}"
            test_url = test_url.replace("{season}", "2024").replace("{league}", "E0")
            test_url = test_url.replace("{date}", "2024-01-01").replace("{sport}", "soccer")
            test_url = test_url.replace("{team_id}", "1").replace("{match_id}", "1")
            test_url = test_url.replace("{event_id}", "1")
            response = requests.get(test_url, timeout=config.get("timeout", 10),
                                     headers={"User-Agent": config.get("user_agent", "KRONOS/1.0")})
            content_type = response.headers.get("Content-Type", "")
            return {"status": "ok" if response.status_code == 200 else "warning",
                    "status_code": response.status_code, "content_type": content_type,
                    "content_length": len(response.content), "test_url": test_url,
                    "has_data": len(response.content) > 100}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _check_rate_limit(self, config):
        rate_limit = config.get("rate_limit", 0)
        return {"status": "ok" if rate_limit > 0 else "warning", "rate_limit": rate_limit,
                "has_burst": "burst" in config or rate_limit > 10,
                "recommendation": "Consider adding rate limiting" if rate_limit == 0 else "OK"}

    def _check_authentication(self, config):
        api_key_ref = config.get("api_key_ref", "")
        import os
        # SourceManager._load_api_keys() zaten config['api_key']'i env veya
        # api_keys.json'dan cozup enjekte ediyor - once ona bak, sadece
        # oncesinde ham env degiskenine bakmak yaniltici "warning" veriyordu.
        has_key = bool(config.get("api_key", "")) or bool(os.getenv(api_key_ref.upper(), ""))
        return {"status": "ok" if has_key else "warning", "api_key_ref": api_key_ref,
                "key_configured": has_key,
                "message": "API key not found (env veya api_keys.json)" if not has_key else "OK"}

    def validate_all(self, sources):
        results = {}
        for source_id, config in sources.items():
            if not config.get("enabled", True):
                continue
            results[source_id] = self.validate_source(source_id, config)
        valid_count = sum(1 for r in results.values() if r.get("status") == "valid")
        return {"total": len(results), "valid": valid_count, "invalid": len(results) - valid_count, "results": results}

    def get_validation_history(self, source_id):
        return [self.validation_results.get(source_id, {})]

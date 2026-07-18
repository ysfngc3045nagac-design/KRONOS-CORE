"""KRONOS_DATA_HUB - Weather API Collector"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
from .base_collector import BaseCollector

class WeatherCollector(BaseCollector):
    def collect(self, venue, lat, lon, match_id=None, **kwargs):
        start_time = datetime.now()
        self.stats["last_run"] = start_time.isoformat()
        try:
            api_key = self._get_api_key()
            if not api_key:
                raise ValueError("Weather API key not configured")
            cache_key = f"{lat}_{lon}_{datetime.now().strftime('%Y%m%d%H')}"
            cached = self.cache.get(self.source_id, cache_key)
            if cached:
                self.stats["cached"] += 1
                return {"status": "cached", "data": cached}
            url = self._build_url("current")
            params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}
            response = self._make_request(url, params=params)
            response.raise_for_status()
            data = self.json_parser.parse(response.content)
            record = self._parse_weather(data, venue, match_id)
            self.cache.set(self.source_id, cache_key, record, ttl=3600)
            self.db.insert("weather", record, conflict_resolution="IGNORE")
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["successful"] += 1
            self.stats["records_collected"] += 1
            self._save_collection_log(f"weather_{venue}", "success", 1, "", elapsed)
            self._update_source_health(True, elapsed)
            return {"status": "success", "data": record, "duration_ms": elapsed}
        except Exception as e:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["failed"] += 1
            self._save_collection_log(f"weather_{venue}", "failed", 0, str(e), elapsed)
            self._update_source_health(False)
            return {"status": "error", "error": str(e), "venue": venue}

    def _get_api_key(self):
        import os
        return os.getenv("WEATHER_API_KEY") or self.config.get("api_key", "")

    def _parse_weather(self, data, venue, match_id):
        main = data.get("main", {})
        wind = data.get("wind", {})
        weather = data.get("weather", [{}])[0]
        return {"match_id": match_id, "venue": venue, "temperature": main.get("temp"), "humidity": main.get("humidity"),
            "wind_speed": wind.get("speed"), "wind_direction": self._degrees_to_direction(wind.get("deg", 0)),
            "precipitation": data.get("rain", {}).get("1h", 0) + data.get("snow", {}).get("1h", 0),
            "visibility": data.get("visibility", 0) / 1000, "condition": weather.get("main", ""),
            "forecast_time": datetime.now().isoformat(), "source_id": self.source_id}

    def _degrees_to_direction(self, degrees):
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(degrees / 22.5) % 16
        return directions[index]

    def parse_response(self, response):
        data = self.json_parser.parse(response.content)
        return [self._parse_weather(data, "", None)]

    def collect_forecast(self, venue, lat, lon, match_id):
        api_key = self._get_api_key()
        if not api_key:
            return {"error": "No API key"}
        url = self._build_url("forecast")
        params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}
        response = self._make_request(url, params=params)
        data = self.json_parser.parse(response.content)
        forecasts = []
        for item in data.get("list", []):
            forecasts.append({"match_id": match_id, "venue": venue, "temperature": item.get("main", {}).get("temp"),
                "humidity": item.get("main", {}).get("humidity"), "wind_speed": item.get("wind", {}).get("speed"),
                "precipitation": item.get("rain", {}).get("3h", 0), "condition": item.get("weather", [{}])[0].get("main", ""),
                "forecast_time": item.get("dt_txt", ""), "source_id": self.source_id})
        return {"forecasts": forecasts, "count": len(forecasts)}

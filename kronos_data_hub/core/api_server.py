"""KRONOS_DATA_HUB - API Server"""
from typing import Dict, Any, Optional
import json
from datetime import datetime

class APIServer:
    def __init__(self, db_manager, source_manager, scheduler, rate_limiter):
        self.db = db_manager
        self.source_manager = source_manager
        self.scheduler = scheduler
        self.rate_limiter = rate_limiter
        self.routes = {}
        self._setup_routes()

    def _setup_routes(self):
        self.routes = {
            "GET /health": self._health_check, "GET /sources": self._list_sources,
            "GET /sources/<id>/health": self._source_health, "GET /matches": self._list_matches,
            "GET /matches/<id>": self._get_match, "GET /odds/<match_id>": self._get_odds,
            "GET /stats": self._system_stats, "POST /collect": self._trigger_collection,
            "GET /scheduler/status": self._scheduler_status
        }

    def _health_check(self):
        return {"status": "ok", "timestamp": datetime.now().isoformat(), "version": "1.0.0"}

    def _list_sources(self):
        sources = self.source_manager.get_all_sources()
        return {"count": len(sources), "sources": {
            k: {"name": v.get("name"), "enabled": v.get("enabled"), "priority": v.get("priority"),
                "data_types": v.get("data_types")} for k, v in sources.items()}}

    def _source_health(self, source_id):
        return self.source_manager.get_source_health(source_id)

    def _list_matches(self, **filters):
        date = filters.get("date", datetime.now().strftime("%Y-%m-%d"))
        matches = self.db.fetch_all(
            """SELECT m.*, ht.name as home_team, at.name as away_team
               FROM matches m LEFT JOIN teams ht ON m.home_team_id = ht.id
               LEFT JOIN teams at ON m.away_team_id = at.id
               WHERE m.match_date = ? ORDER BY m.match_time""", (date,))
        return {"date": date, "count": len(matches), "matches": matches}

    def _get_match(self, match_id):
        match = self.db.fetch_one(
            """SELECT m.*, ht.name as home_team, at.name as away_team
               FROM matches m LEFT JOIN teams ht ON m.home_team_id = ht.id
               LEFT JOIN teams at ON m.away_team_id = at.id WHERE m.id = ?""", (match_id,))
        if not match:
            return {"error": "Match not found"}
        stats = self.db.fetch_all("SELECT * FROM match_statistics WHERE match_id = ?", (match_id,))
        odds = self.db.fetch_all("SELECT * FROM odds WHERE match_id = ? ORDER BY timestamp DESC", (match_id,))
        match["statistics"] = stats
        match["odds"] = odds
        return match

    def _get_odds(self, match_id):
        odds = self.db.fetch_all("SELECT * FROM odds WHERE match_id = ? ORDER BY timestamp DESC LIMIT 50", (match_id,))
        return {"match_id": match_id, "count": len(odds), "latest_odds": odds[:5] if odds else []}

    def _system_stats(self):
        return {
            "sources": self.source_manager.get_stats(),
            "scheduler": self.scheduler.get_status() if self.scheduler else None,
            "rate_limiter": self.rate_limiter.get_global_stats() if self.rate_limiter else None,
            "database": {"matches": self.db.get_row_count("matches"), "teams": self.db.get_row_count("teams"),
                         "odds": self.db.get_row_count("odds")}
        }

    def _trigger_collection(self, **params):
        source_id = params.get("source_id")
        if source_id:
            collector = self.source_manager.get_collector(source_id)
            if collector:
                result = collector.collect()
                return {"triggered": True, "result": result}
        return {"error": "Source not found or not configured"}

    def _scheduler_status(self):
        return self.scheduler.get_status() if self.scheduler else {"error": "Scheduler not running"}

    def handle_request(self, method, path, **kwargs):
        route_key = f"{method} {path}"
        handler = self.routes.get(route_key)
        if handler:
            return handler(**kwargs)
        return {"error": "Route not found"}

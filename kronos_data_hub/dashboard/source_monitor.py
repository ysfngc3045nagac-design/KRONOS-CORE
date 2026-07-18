"""KRONOS_DATA_HUB - Source Monitor Dashboard"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class SourceMonitor:
    def __init__(self, db_manager, source_manager):
        self.db = db_manager
        self.source_manager = source_manager

    def get_dashboard_data(self):
        return {"summary": self._get_summary(), "source_status": self._get_source_status(),
                "recent_activity": self._get_recent_activity(), "alerts": self._get_alerts(),
                "performance": self._get_performance_metrics()}

    def _get_summary(self):
        total_sources = len(self.source_manager.get_all_sources())
        enabled = len(self.source_manager.get_enabled_sources())
        total_matches = self.db.get_row_count("matches") or 0
        total_teams = self.db.get_row_count("teams") or 0
        total_odds = self.db.get_row_count("odds") or 0
        today = datetime.now().strftime("%Y-%m-%d")
        today_matches = self.db.fetch_scalar("SELECT COUNT(*) FROM matches WHERE match_date = ?", (today,)) or 0
        return {"sources": {"total": total_sources, "enabled": enabled},
                "database": {"matches": total_matches, "teams": total_teams, "odds": total_odds, "today_matches": today_matches},
                "timestamp": datetime.now().isoformat()}

    def _get_source_status(self):
        health_data = self.db.fetch_all(
            """SELECT * FROM source_health ORDER BY
               CASE status WHEN 'down' THEN 1 WHEN 'degraded' THEN 2 ELSE 3 END, updated_at DESC""")
        sources = self.source_manager.get_all_sources()
        result = []
        for health in health_data:
            source_id = health["source_id"]
            config = sources.get(source_id, {})
            result.append({"source_id": source_id, "name": config.get("name", source_id), "status": health["status"],
                "uptime": health["uptime_percentage"], "last_check": health["last_check"],
                "last_success": health["last_success"], "error_rate": health["error_rate"],
                "avg_response": health["avg_response_time_ms"], "priority": config.get("priority", 5),
                "enabled": config.get("enabled", True)})
        return result

    def _get_recent_activity(self, limit=20):
        return self.db.fetch_all("SELECT * FROM collection_logs ORDER BY created_at DESC LIMIT ?", (limit,))

    def _get_alerts(self):
        alerts = []
        down_sources = self.db.fetch_all("SELECT * FROM source_health WHERE status = 'down'")
        for source in down_sources:
            alerts.append({"level": "critical", "type": "source_down", "source_id": source["source_id"],
                "message": f"Source {source['source_id']} is down", "since": source["last_failure"]})
        degraded = self.db.fetch_all("SELECT * FROM source_health WHERE status = 'degraded'")
        for source in degraded:
            alerts.append({"level": "warning", "type": "source_degraded", "source_id": source["source_id"],
                "message": f"Source {source['source_id']} is degraded ({source['uptime_percentage']:.1f}% uptime)",
                "since": source["last_failure"]})
        recent_failures = self.db.fetch_all(
            """SELECT source_id, COUNT(*) as count FROM collection_logs
               WHERE status = 'failed' AND created_at > datetime('now', '-1 hour') GROUP BY source_id""")
        for failure in recent_failures:
            if failure["count"] >= 3:
                alerts.append({"level": "warning", "type": "multiple_failures", "source_id": failure["source_id"],
                    "message": f"{failure['count']} failures in last hour", "count": failure["count"]})
        return sorted(alerts, key=lambda x: {"critical": 0, "warning": 1, "info": 2}[x["level"]])

    def _get_performance_metrics(self):
        since = (datetime.now() - timedelta(hours=24)).isoformat()
        hourly = self.db.fetch_all(
            """SELECT strftime('%H', created_at) as hour, COUNT(*) as requests,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success, AVG(duration_ms) as avg_duration
            FROM collection_logs WHERE created_at > ? GROUP BY hour ORDER BY hour""", (since,))
        total = sum(h["requests"] for h in hourly)
        success = sum(h["success"] for h in hourly)
        return {"period": "last_24h", "total_requests": total,
                "success_rate": round(success / total * 100, 2) if total > 0 else 0,
                "avg_duration_ms": round(sum(h["avg_duration"] or 0 for h in hourly) / max(len(hourly), 1), 2),
                "hourly_breakdown": hourly}

    def get_source_detail(self, source_id):
        health = self.db.fetch_one("SELECT * FROM source_health WHERE source_id = ?", (source_id,))
        if not health:
            return {"error": "Source not found"}
        logs = self.db.fetch_all(
            "SELECT * FROM collection_logs WHERE source_id = ? AND created_at > date('now', '-30 days') ORDER BY created_at DESC", (source_id,))
        daily = self.db.fetch_all(
            """SELECT date(created_at) as day, COUNT(*) as runs,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success, SUM(records_count) as total_records
            FROM collection_logs WHERE source_id = ? AND created_at > date('now', '-30 days')
            GROUP BY date(created_at) ORDER BY day DESC""", (source_id,))
        return {"source_id": source_id, "health": dict(health), "recent_logs": logs[:10],
                "daily_summary": daily, "total_logs_30d": len(logs)}

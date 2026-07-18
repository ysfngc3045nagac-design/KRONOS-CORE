"""KRONOS_DATA_HUB - Source Health"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class SourceHealthMonitor:
    def __init__(self, db_manager):
        self.db = db_manager
        self.status_thresholds = {
            "healthy": {"error_rate": 0.1, "min_success_rate": 0.9},
            "degraded": {"error_rate": 0.3, "min_success_rate": 0.7},
            "down": {"error_rate": 0.5, "min_success_rate": 0.5}
        }

    def check_source(self, source_id):
        since = (datetime.now() - timedelta(days=7)).isoformat()
        stats = self.db.fetch_one(
            """SELECT COUNT(*) as total, SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                AVG(duration_ms) as avg_duration, MAX(created_at) as last_success
            FROM collection_logs WHERE source_id = ? AND created_at > ?""", (source_id, since))
        if not stats or stats["total"] == 0:
            return {"source_id": source_id, "status": "unknown", "message": "No recent data"}
        total = stats["total"]
        success = stats["success"] or 0
        error_rate = 1 - (success / total)
        avg_duration = stats["avg_duration"] or 0
        if error_rate <= self.status_thresholds["healthy"]["error_rate"]:
            status = "healthy"
        elif error_rate <= self.status_thresholds["degraded"]["error_rate"]:
            status = "degraded"
        else:
            status = "down"
        uptime = (success / total) * 100
        return {"source_id": source_id, "status": status, "total_runs": total, "successful_runs": success,
                "error_rate": round(error_rate, 3), "uptime_percent": round(uptime, 2),
                "avg_duration_ms": round(avg_duration, 2), "last_success": stats["last_success"],
                "checked_at": datetime.now().isoformat()}

    def check_all_sources(self):
        sources = self.db.fetch_all("SELECT DISTINCT source_id FROM collection_logs WHERE created_at > date('now', '-30 days')")
        results = []
        for source in sources:
            result = self.check_source(source["source_id"])
            results.append(result)
            self._update_health_db(result)
        return results

    def _update_health_db(self, result):
        existing = self.db.fetch_one("SELECT id FROM source_health WHERE source_id = ?", (result["source_id"],))
        if existing:
            self.db.execute(
                """UPDATE source_health SET status = ?, last_check = ?, last_success = ?,
                   error_rate = ?, uptime_percentage = ?, avg_response_time_ms = ?, updated_at = ?
                   WHERE source_id = ?""",
                (result["status"], result["checked_at"], result["last_success"], result["error_rate"],
                 result["uptime_percent"], result["avg_duration_ms"], datetime.now().isoformat(), result["source_id"]))
        else:
            self.db.execute(
                """INSERT INTO source_health (source_id, status, last_check, last_success,
                    error_rate, uptime_percentage, avg_response_time_ms) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (result["source_id"], result["status"], result["checked_at"], result["last_success"],
                 result["error_rate"], result["uptime_percent"], result["avg_duration_ms"]))

    def get_health_summary(self):
        all_health = self.check_all_sources()
        status_counts = {"healthy": 0, "degraded": 0, "down": 0, "unknown": 0}
        for h in all_health:
            status_counts[h["status"]] += 1
        return {"total_sources": len(all_health), "status_breakdown": status_counts,
                "healthy_percent": round(status_counts["healthy"] / len(all_health) * 100, 2) if all_health else 0,
                "sources": all_health}

    def get_recommendations(self):
        recommendations = []
        all_health = self.check_all_sources()
        for health in all_health:
            if health["status"] == "down":
                recommendations.append({"source_id": health["source_id"], "priority": "critical",
                    "action": "disable_source", "reason": f"Source is down with {health['error_rate']*100:.1f}% error rate"})
            elif health["status"] == "degraded":
                recommendations.append({"source_id": health["source_id"], "priority": "high",
                    "action": "investigate", "reason": f"Source degraded, uptime: {health['uptime_percent']:.1f}%"})
            elif health["uptime_percent"] < 95:
                recommendations.append({"source_id": health["source_id"], "priority": "medium",
                    "action": "monitor", "reason": f"Uptime below 95%: {health['uptime_percent']:.1f}%"})
        return sorted(recommendations, key=lambda x: x["priority"])

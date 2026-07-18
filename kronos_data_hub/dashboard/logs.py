"""KRONOS_DATA_HUB - Log Manager"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class LogManager:
    def __init__(self, db_manager):
        self.db = db_manager

    def get_logs(self, source_id=None, status=None, since=None, limit=100):
        conditions = []
        params = []
        if source_id:
            conditions.append("source_id = ?")
            params.append(source_id)
        if status:
            conditions.append("status = ?")
            params.append(status)
        if since:
            conditions.append("created_at > ?")
            params.append(since)
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        query = f"SELECT * FROM collection_logs {where} ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        return self.db.fetch_all(query, tuple(params))

    def get_errors(self, source_id=None, hours=24, limit=50):
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        conditions = ["status = 'failed'", "created_at > ?"]
        params = [since]
        if source_id:
            conditions.append("source_id = ?")
            params.append(source_id)
        where = "WHERE " + " AND ".join(conditions)
        return self.db.fetch_all(f"SELECT * FROM collection_logs {where} ORDER BY created_at DESC LIMIT ?", tuple(params + [limit]))

    def get_error_summary(self, hours=24):
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        errors = self.db.fetch_all(
            """SELECT source_id, COUNT(*) as count, error_message FROM collection_logs
               WHERE status = 'failed' AND created_at > ? GROUP BY source_id, error_message ORDER BY count DESC""", (since,))
        total_errors = sum(e["count"] for e in errors)
        by_source = {}
        for error in errors:
            sid = error["source_id"]
            by_source[sid] = by_source.get(sid, 0) + error["count"]
        return {"period_hours": hours, "total_errors": total_errors, "unique_errors": len(errors),
                "by_source": by_source, "top_errors": errors[:10]}

    def get_success_rate(self, source_id=None, hours=24):
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        if source_id:
            stats = self.db.fetch_one(
                "SELECT COUNT(*) as total, SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success FROM collection_logs WHERE source_id = ? AND created_at > ?",
                (source_id, since))
            return {"source_id": source_id, "period_hours": hours, "total": stats["total"], "success": stats["success"],
                    "rate": round(stats["success"] / max(stats["total"], 1) * 100, 2)}
        all_stats = self.db.fetch_all(
            "SELECT source_id, COUNT(*) as total, SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success FROM collection_logs WHERE created_at > ? GROUP BY source_id",
            (since,))
        return {"period_hours": hours, "sources": {s["source_id"]: {"total": s["total"], "success": s["success"],
                "rate": round(s["success"] / max(s["total"], 1) * 100, 2)} for s in all_stats}}

    def clear_old_logs(self, days=30):
        since = (datetime.now() - timedelta(days=days)).isoformat()
        result = self.db.execute("DELETE FROM collection_logs WHERE created_at < ?", (since,))
        return result.rowcount if hasattr(result, 'rowcount') else 0

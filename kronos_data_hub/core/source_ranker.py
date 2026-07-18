"""KRONOS_DATA_HUB - Source Ranker"""
from typing import Dict, List, Any, Optional
from datetime import datetime

class SourceRanker:
    def __init__(self, db_manager):
        self.db = db_manager

    def rank_sources(self, data_type=None, league=None, min_score=0.0):
        since = datetime.now().isoformat()[:10] + "T00:00:00"
        query = """
            SELECT source_id, COUNT(*) as total_runs,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                AVG(CASE WHEN status = 'success' THEN records_count ELSE 0 END) as avg_records,
                AVG(CASE WHEN status = 'success' THEN duration_ms ELSE NULL END) as avg_duration,
                MAX(created_at) as last_run
            FROM collection_logs WHERE created_at > ? GROUP BY source_id
        """
        rows = self.db.fetch_all(query, (since,))
        ranked = []
        for row in rows:
            source_id = row["source_id"]
            total = row["total_runs"] or 1
            success = row["success_count"] or 0
            success_rate = success / total
            avg_records = row["avg_records"] or 0
            avg_duration = row["avg_duration"] or 10000
            last_run = row["last_run"]
            freshness = 1.0
            if last_run:
                try:
                    last_dt = datetime.fromisoformat(last_run)
                    hours_ago = (datetime.now() - last_dt).total_seconds() / 3600
                    freshness = max(0, 1 - hours_ago / 168)
                except:
                    pass
            score = (success_rate * 0.40 + min(avg_records / 500, 1.0) * 0.25 +
                     max(0, 1 - avg_duration / 10000) * 0.20 + freshness * 0.15)
            if score >= min_score:
                ranked.append({
                    "source_id": source_id, "score": round(score, 3),
                    "success_rate": round(success_rate, 3), "avg_records": round(avg_records, 1),
                    "avg_duration_ms": round(avg_duration, 1), "freshness": round(freshness, 3),
                    "total_runs": total, "last_run": last_run
                })
        ranked.sort(key=lambda x: x["score"], reverse=True)
        for i, item in enumerate(ranked):
            item["rank"] = i + 1
        return ranked

    def get_top_sources(self, n=5, data_type=None):
        all_ranked = self.rank_sources(data_type=data_type)
        return all_ranked[:n]

    def get_source_trend(self, source_id, days=30):
        since = datetime.now().isoformat()[:10] + "T00:00:00"
        daily = self.db.fetch_all(
            """SELECT date(created_at) as day, COUNT(*) as runs,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                AVG(records_count) as avg_records
            FROM collection_logs WHERE source_id = ? AND created_at > ?
            GROUP BY date(created_at) ORDER BY day""", (source_id, since))
        if not daily:
            return {"error": "No data available"}
        success_rates = [d["success"] / max(d["runs"], 1) for d in daily]
        avg_success = sum(success_rates) / len(success_rates)
        if len(success_rates) >= 3:
            recent = sum(success_rates[-3:]) / 3
            older = sum(success_rates[:3]) / 3
            trend = "improving" if recent > older else "declining" if recent < older else "stable"
        else:
            trend = "insufficient_data"
        return {"source_id": source_id, "days_analyzed": len(daily), "avg_success_rate": round(avg_success, 3),
                "trend": trend, "daily_breakdown": daily}

    def compare_sources(self, source_ids):
        comparison = {}
        for source_id in source_ids:
            ranking = self.rank_sources(min_score=0)
            source_rank = next((r for r in ranking if r["source_id"] == source_id), None)
            if source_rank:
                trend = self.get_source_trend(source_id)
                comparison[source_id] = {"rank": source_rank.get("rank"), "score": source_rank.get("score"),
                                          "success_rate": source_rank.get("success_rate"), "trend": trend.get("trend", "unknown")}
        return {"compared_sources": list(comparison.keys()), "comparison": comparison,
                "best_overall": max(comparison, key=lambda x: comparison[x]["score"]) if comparison else None}

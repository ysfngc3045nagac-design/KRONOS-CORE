"""KRONOS_DATA_HUB - Source AI"""
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class SourceAI:
    def __init__(self, db_manager):
        self.db = db_manager
        self.weights = {"freshness": 0.25, "accuracy": 0.25, "coverage": 0.20, "reliability": 0.15, "speed": 0.10, "consistency": 0.05}

    def evaluate_source(self, source_id):
        since = (datetime.now() - timedelta(days=30)).isoformat()
        logs = self.db.fetch_all("SELECT * FROM collection_logs WHERE source_id = ? AND created_at > ? ORDER BY created_at DESC", (source_id, since))
        if not logs:
            return {"error": "No data available for evaluation"}
        freshness = self._calculate_freshness(logs)
        accuracy = self._calculate_accuracy(logs)
        coverage = self._calculate_coverage(source_id, since)
        reliability = self._calculate_reliability(logs)
        speed = self._calculate_speed(logs)
        consistency = self._calculate_consistency(logs)
        overall_score = (freshness * self.weights["freshness"] + accuracy * self.weights["accuracy"] +
            coverage * self.weights["coverage"] + reliability * self.weights["reliability"] +
            speed * self.weights["speed"] + consistency * self.weights["consistency"])
        return {"source_id": source_id, "overall_score": round(overall_score * 100, 2),
            "scores": {"freshness": round(freshness * 100, 2), "accuracy": round(accuracy * 100, 2),
                "coverage": round(coverage * 100, 2), "reliability": round(reliability * 100, 2),
                "speed": round(speed * 100, 2), "consistency": round(consistency * 100, 2)},
            "recommendation": self._get_recommendation(overall_score), "evaluated_at": datetime.now().isoformat()}

    def _calculate_freshness(self, logs):
        if not logs:
            return 0.0
        successful = [l for l in logs if l["status"] == "success"]
        if not successful:
            return 0.0
        last_success = datetime.fromisoformat(successful[0]["created_at"])
        hours_ago = (datetime.now() - last_success).total_seconds() / 3600
        return max(0, 1 - (hours_ago / 168))

    def _calculate_accuracy(self, logs):
        if not logs:
            return 0.0
        total = len(logs)
        success = len([l for l in logs if l["status"] == "success"])
        return success / total if total > 0 else 0.0

    def _calculate_coverage(self, source_id, since):
        total_records = self.db.fetch_scalar(
            "SELECT SUM(records_count) FROM collection_logs WHERE source_id = ? AND status = 'success' AND created_at > ?",
            (source_id, since)) or 0
        expected = self._get_expected_records(source_id)
        return min(1.0, total_records / expected) if expected > 0 else 0.0

    def _calculate_reliability(self, logs):
        if not logs:
            return 0.0
        recent = logs[:10]
        success_streak = 0
        for log in recent:
            if log["status"] == "success":
                success_streak += 1
            else:
                break
        return min(1.0, success_streak / 5)

    def _calculate_speed(self, logs):
        success_logs = [l for l in logs if l["status"] == "success" and l["duration_ms"]]
        if not success_logs:
            return 0.0
        avg_duration = sum(l["duration_ms"] for l in success_logs) / len(success_logs)
        return max(0, 1 - (avg_duration / 10000))

    def _calculate_consistency(self, logs):
        success_logs = [l for l in logs if l["status"] == "success"]
        if len(success_logs) < 2:
            return 0.5
        counts = [l["records_count"] for l in success_logs if l["records_count"]]
        if not counts:
            return 0.5
        avg = sum(counts) / len(counts)
        variance = sum((c - avg) ** 2 for c in counts) / len(counts)
        std_dev = variance ** 0.5
        cv = std_dev / avg if avg > 0 else 0
        return max(0, 1 - cv)

    def _get_expected_records(self, source_id):
        expectations = {"fbref": 500, "understat": 400, "football_data": 1000, "odds_api": 2000,
            "sofascore": 1500, "fotmob": 1000, "clubelo": 500, "transfermarkt": 300, "weather_api": 100,
            "news_api": 500, "injuries_api": 200, "flashscore": 2000, "openfootball": 100, "github_sources": 50}
        return expectations.get(source_id, 100)

    def _get_recommendation(self, score):
        if score >= 0.8:
            return "Excellent source - Primary data source recommended"
        elif score >= 0.6:
            return "Good source - Use with standard validation"
        elif score >= 0.4:
            return "Fair source - Use as secondary source only"
        else:
            return "Poor source - Consider disabling or investigating"

    def rank_sources(self, source_ids=None):
        if source_ids is None:
            rows = self.db.fetch_all("SELECT DISTINCT source_id FROM collection_logs")
            source_ids = [r["source_id"] for r in rows]
        results = []
        for source_id in source_ids:
            evaluation = self.evaluate_source(source_id)
            if "error" not in evaluation:
                results.append(evaluation)
        results.sort(key=lambda x: x["overall_score"], reverse=True)
        return results

    def get_best_source_for_data_type(self, data_type):
        source_specialties = {"xG": ["understat", "fbref"], "advanced_stats": ["fbref", "sofascore"],
            "odds": ["odds_api"], "live_scores": ["sofascore", "flashscore", "fotmob"], "elo": ["clubelo"],
            "transfers": ["transfermarkt"], "injuries": ["injuries_api", "news_api"], "weather": ["weather_api"],
            "historical": ["football_data", "openfootball"]}
        candidates = source_specialties.get(data_type, [])
        if not candidates:
            return None
        rankings = self.rank_sources(candidates)
        return rankings[0]["source_id"] if rankings else None

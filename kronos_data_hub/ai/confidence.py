"""KRONOS_DATA_HUB - Confidence Scorer"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class ConfidenceScorer:
    def __init__(self, db_manager):
        self.db = db_manager

    def calculate_match_confidence(self, match_id):
        scores = {}
        sources = self.db.fetch_all(
            """SELECT DISTINCT source_id FROM matches WHERE id = ?
               UNION SELECT DISTINCT source_id FROM match_statistics WHERE match_id = ?
               UNION SELECT DISTINCT source_id FROM odds WHERE match_id = ?""", (match_id, match_id, match_id))
        scores["source_count"] = min(len(sources) / 5, 1.0)
        match = self.db.fetch_one("SELECT * FROM matches WHERE id = ?", (match_id,))
        if match:
            required_fields = ["home_goals", "away_goals", "match_date", "venue"]
            filled = sum(1 for f in required_fields if match.get(f) is not None)
            scores["completeness"] = filled / len(required_fields)
        else:
            scores["completeness"] = 0.0
        stats_count = self.db.fetch_scalar("SELECT COUNT(*) FROM match_statistics WHERE match_id = ?", (match_id,)) or 0
        scores["stat_depth"] = min(stats_count / 20, 1.0)
        odds_count = self.db.fetch_scalar("SELECT COUNT(DISTINCT bookmaker) FROM odds WHERE match_id = ?", (match_id,)) or 0
        scores["odds_coverage"] = min(odds_count / 5, 1.0)
        if match and match.get("updated_at"):
            last_update = datetime.fromisoformat(match["updated_at"])
            hours_ago = (datetime.now() - last_update).total_seconds() / 3600
            scores["freshness"] = max(0, 1 - (hours_ago / 72))
        else:
            scores["freshness"] = 0.5
        weights = {"source_count": 0.25, "completeness": 0.20, "stat_depth": 0.20, "odds_coverage": 0.20, "freshness": 0.15}
        overall = sum(scores[k] * weights[k] for k in weights)
        return {"match_id": match_id, "overall_score": round(overall, 3),
                "component_scores": {k: round(v, 3) for k, v in scores.items()},
                "confidence_level": self._level(overall), "calculated_at": datetime.now().isoformat()}

    def calculate_source_confidence(self, source_id):
        since = (datetime.now() - timedelta(days=30)).isoformat()
        total = self.db.fetch_scalar("SELECT COUNT(*) FROM collection_logs WHERE source_id = ? AND created_at > ?", (source_id, since)) or 0
        success = self.db.fetch_scalar("SELECT COUNT(*) FROM collection_logs WHERE source_id = ? AND status = 'success' AND created_at > ?", (source_id, since)) or 0
        success_rate = success / total if total > 0 else 0
        avg_records = self.db.fetch_scalar("SELECT AVG(records_count) FROM collection_logs WHERE source_id = ? AND status = 'success' AND created_at > ?", (source_id, since)) or 0
        errors = self.db.fetch_scalar("SELECT COUNT(*) FROM collection_logs WHERE source_id = ? AND status = 'failed' AND created_at > ?", (source_id, since)) or 0
        error_rate = errors / total if total > 0 else 0
        scores = {"success_rate": success_rate, "avg_records": min(avg_records / 500, 1.0), "error_rate": max(0, 1 - error_rate * 5)}
        overall = (scores["success_rate"] * 0.5 + scores["avg_records"] * 0.25 + scores["error_rate"] * 0.25)
        return {"source_id": source_id, "overall_score": round(overall, 3),
                "component_scores": {k: round(v, 3) for k, v in scores.items()},
                "confidence_level": self._level(overall), "calculated_at": datetime.now().isoformat()}

    def calculate_odds_confidence(self, match_id):
        odds = self.db.fetch_all("SELECT * FROM odds WHERE match_id = ? ORDER BY timestamp DESC", (match_id,))
        if not odds:
            return {"match_id": match_id, "overall_score": 0, "reason": "No odds data"}
        bookmakers = len(set(o["bookmaker"] for o in odds))
        home_odds = [o["home_odds"] for o in odds if o.get("home_odds")]
        if home_odds:
            import statistics
            try:
                cv = statistics.stdev(home_odds) / statistics.mean(home_odds)
                consistency = max(0, 1 - cv)
            except:
                consistency = 0.5
        else:
            consistency = 0
        latest = max(o["timestamp"] for o in odds if o.get("timestamp"))
        hours_ago = (datetime.now() - datetime.fromisoformat(latest)).total_seconds() / 3600
        freshness = max(0, 1 - (hours_ago / 24))
        scores = {"bookmaker_count": min(bookmakers / 5, 1.0), "odds_consistency": consistency, "freshness": freshness}
        overall = (scores["bookmaker_count"] * 0.4 + scores["odds_consistency"] * 0.4 + scores["freshness"] * 0.2)
        return {"match_id": match_id, "overall_score": round(overall, 3),
                "component_scores": {k: round(v, 3) for k, v in scores.items()},
                "confidence_level": self._level(overall), "calculated_at": datetime.now().isoformat()}

    def _level(self, score):
        if score >= 0.8:
            return "high"
        elif score >= 0.6:
            return "medium"
        elif score >= 0.4:
            return "low"
        else:
            return "very_low"

    def get_low_confidence_matches(self, threshold=0.5):
        matches = self.db.fetch_all("SELECT id FROM matches WHERE status IN ('scheduled', 'live')")
        low_confidence = []
        for match in matches:
            conf = self.calculate_match_confidence(match["id"])
            if conf["overall_score"] < threshold:
                low_confidence.append(conf)
        return sorted(low_confidence, key=lambda x: x["overall_score"])

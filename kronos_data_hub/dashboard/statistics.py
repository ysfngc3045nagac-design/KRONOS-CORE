"""KRONOS_DATA_HUB - Statistics Dashboard"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class StatisticsPanel:
    def __init__(self, db_manager):
        self.db = db_manager

    def get_overview(self):
        return {"matches": self._get_match_stats(), "teams": self._get_team_stats(),
                "odds": self._get_odds_stats(), "sources": self._get_source_stats(),
                "data_quality": self._get_quality_stats()}

    def _get_match_stats(self):
        total = self.db.get_row_count("matches")
        today = datetime.now().strftime("%Y-%m-%d")
        today_count = self.db.fetch_scalar("SELECT COUNT(*) FROM matches WHERE match_date = ?", (today,)) or 0
        by_status = self.db.fetch_all("SELECT status, COUNT(*) as count FROM matches GROUP BY status")
        by_league = self.db.fetch_all(
            "SELECT l.name, COUNT(*) as count FROM matches m JOIN leagues l ON m.league_id = l.id GROUP BY l.name ORDER BY count DESC LIMIT 10")
        return {"total": total, "today": today_count, "by_status": {r["status"]: r["count"] for r in by_status}, "top_leagues": by_league}

    def _get_team_stats(self):
        total = self.db.get_row_count("teams")
        by_country = self.db.fetch_all("SELECT country, COUNT(*) as count FROM teams WHERE country IS NOT NULL GROUP BY country ORDER BY count DESC LIMIT 10")
        top_elo = self.db.fetch_all("SELECT name, elo_rating FROM teams ORDER BY elo_rating DESC LIMIT 10")
        return {"total": total, "by_country": by_country, "top_elo": top_elo}

    def _get_odds_stats(self):
        total = self.db.get_row_count("odds")
        by_bookmaker = self.db.fetch_all("SELECT bookmaker, COUNT(*) as count FROM odds GROUP BY bookmaker ORDER BY count DESC LIMIT 10")
        latest_odds = self.db.fetch_all("SELECT * FROM odds ORDER BY timestamp DESC LIMIT 5")
        return {"total": total, "by_bookmaker": by_bookmaker, "latest": latest_odds}

    def _get_source_stats(self):
        since = (datetime.now() - timedelta(days=7)).isoformat()
        return self.db.fetch_all(
            """SELECT source_id, COUNT(*) as total_runs, SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                SUM(records_count) as total_records FROM collection_logs WHERE created_at > ? GROUP BY source_id ORDER BY total_runs DESC""",
            (since,))

    def _get_quality_stats(self):
        match_nulls = self.db.fetch_scalar("SELECT COUNT(*) FROM matches WHERE home_goals IS NULL AND away_goals IS NULL") or 0
        total_matches = self.db.get_row_count("matches")
        return {"match_null_rate": round(match_nulls / max(total_matches, 1) * 100, 2), "total_matches": total_matches, "unscored_matches": match_nulls}

    def get_daily_report(self, date=None):
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        matches = self.db.fetch_all("SELECT * FROM matches WHERE match_date = ? ORDER BY match_time", (date,))
        collections = self.db.fetch_all("SELECT * FROM collection_logs WHERE date(created_at) = ? ORDER BY created_at DESC", (date,))
        return {"date": date, "matches": {"count": len(matches),
                "scheduled": len([m for m in matches if m.get("status") == "scheduled"]),
                "live": len([m for m in matches if m.get("status") == "live"]),
                "finished": len([m for m in matches if m.get("status") == "finished"])},
                "collections": {"count": len(collections),
                "successful": len([c for c in collections if c.get("status") == "success"]),
                "failed": len([c for c in collections if c.get("status") == "failed"]),
                "total_records": sum(c.get("records_count", 0) for c in collections)}}

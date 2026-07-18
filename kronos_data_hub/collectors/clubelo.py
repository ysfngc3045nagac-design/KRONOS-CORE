"""KRONOS_DATA_HUB - ClubELO Collector"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
from .base_collector import BaseCollector

class ClubELOCollector(BaseCollector):
    def collect(self, team=None, **kwargs):
        start_time = datetime.now()
        self.stats["last_run"] = start_time.isoformat()
        try:
            if team:
                url = self._build_url("rankings", team=team)
            else:
                url = self._build_url("all_rankings")
            response = self._make_request(url)
            response.raise_for_status()
            records = self.parse_response(response)
            saved = self._save_elo_ratings(records)
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["successful"] += 1
            self.stats["records_collected"] += saved
            self._save_collection_log(f"clubelo_{team or 'all'}", "success", saved, "", elapsed)
            self._update_source_health(True, elapsed)
            return {"status": "success", "records": saved, "team": team, "duration_ms": elapsed}
        except Exception as e:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["failed"] += 1
            self._save_collection_log(f"clubelo_{team or 'all'}", "failed", 0, str(e), elapsed)
            self._update_source_health(False)
            return {"status": "error", "error": str(e), "team": team}

    def parse_response(self, response):
        content = response.content.decode("utf-8", errors="ignore")
        records = self.csv_parser.parse(content)
        normalized = []
        for record in records:
            normalized.append({"rank": record.get("rank"), "club": record.get("club", ""),
                "country": record.get("country", ""), "level": record.get("level"), "elo": record.get("elo"),
                "from": record.get("from"), "to": record.get("to"), "source_id": self.source_id,
                "collected_at": datetime.now().isoformat()})
        return normalized

    def _save_elo_ratings(self, records):
        saved = 0
        for record in records:
            if not record.get("club"):
                continue
            self.db.execute("UPDATE teams SET elo_rating = ? WHERE name LIKE ? OR short_name LIKE ?",
                (record.get("elo", 1500), f"%{record['club']}%", f"%{record['club']}%"))
            saved += 1
        return saved

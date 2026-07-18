"""KRONOS_DATA_HUB - Sofascore Collector"""
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import requests
from .base_collector import BaseCollector

class SofascoreCollector(BaseCollector):
    def collect(self, date=None, **kwargs):
        start_time = datetime.now()
        self.stats["last_run"] = start_time.isoformat()
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            url = self._build_url("events", date=date)
            response = self._make_request(url)
            response.raise_for_status()
            data = self.json_parser.parse(response.content)
            events = data.get("events", []) if isinstance(data, dict) else []
            records = self._parse_events(events)
            saved = self._save_events(records)
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["successful"] += 1
            self.stats["records_collected"] += saved
            self._save_collection_log(f"sofascore_{date}", "success", saved, "", elapsed)
            self._update_source_health(True, elapsed)
            return {"status": "success", "records": saved, "date": date, "duration_ms": elapsed}
        except Exception as e:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["failed"] += 1
            self._save_collection_log(f"sofascore_{date or 'today'}", "failed", 0, str(e), elapsed)
            self._update_source_health(False)
            return {"status": "error", "error": str(e), "date": date}

    def _parse_events(self, events):
        records = []
        for event in events:
            tournament = event.get("tournament", {})
            home_team = event.get("homeTeam", {})
            away_team = event.get("awayTeam", {})
            status = event.get("status", {})
            records.append({
                "event_id": event.get("id"), "tournament": tournament.get("name", ""),
                "category": tournament.get("category", {}).get("name", ""),
                "match_date": datetime.fromtimestamp(event.get("startTimestamp", 0)).strftime("%Y-%m-%d"),
                "match_time": datetime.fromtimestamp(event.get("startTimestamp", 0)).strftime("%H:%M"),
                "home_team": home_team.get("name", ""), "away_team": away_team.get("name", ""),
                "home_goals": event.get("homeScore", {}).get("current"), "away_goals": event.get("awayScore", {}).get("current"),
                "status": status.get("type", ""), "status_description": status.get("description", ""),
                "venue": event.get("venue", {}).get("stadium", {}).get("name", ""), "referee": event.get("referee", {}).get("name", ""),
                "source_id": self.source_id, "collected_at": datetime.now().isoformat()
            })
        return records

    def _save_events(self, records):
        saved = 0
        for record in records:
            if not record.get("home_team") or not record.get("away_team"):
                continue
            self.db.insert("matches", {"source_id": self.source_id, "source_match_id": str(record.get("event_id", "")),
                "match_date": record.get("match_date", ""), "match_time": record.get("match_time", ""),
                "home_goals": record.get("home_goals"), "away_goals": record.get("away_goals"),
                "status": self._map_status(record.get("status", "")), "venue": record.get("venue", ""),
                "referee": record.get("referee", ""), "is_processed": 0}, conflict_resolution="IGNORE")
            saved += 1
        return saved

    def _map_status(self, status):
        status_map = {"notstarted": "scheduled", "inprogress": "live", "finished": "finished",
                      "postponed": "postponed", "cancelled": "cancelled"}
        return status_map.get(status.lower(), status)

    def collect_event_details(self, event_id):
        url = self._build_url("event_details", event_id=event_id)
        response = self._make_request(url)
        data = self.json_parser.parse(response.content)
        return data if data else {}

    def parse_response(self, response):
        data = self.json_parser.parse(response.content)
        events = data.get("events", []) if isinstance(data, dict) else []
        return self._parse_events(events)

"""
KRONOS_DATA_HUB - Football-Data.org Collector (api.football-data.org/v4)

DIKKAT: Mevcut football_data.py dosyasi Football-Data.CO.UK'e ait (CSV tabanli,
anahtar gerektirmez). Bu dosya ise Football-Data.ORG'a ait - farkli sirket,
farkli API, JSON tabanli, header uzerinden anahtar ister ('X-Auth-Token').
Ikisini birbirine karistirmayin.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from .base_collector import BaseCollector


class FootballDataOrgCollector(BaseCollector):
    COMPETITION_CODES = {
        "premier_league": "PL", "la_liga": "PD", "bundesliga": "BL1",
        "serie_a": "SA", "ligue_1": "FL1", "champions_league": "CL",
        "eredivisie": "DED", "primeira_liga": "PPL",
    }

    def collect(self, competition="premier_league", season=None, **kwargs):
        start_time = datetime.now()
        self.stats["last_run"] = start_time.isoformat()
        try:
            api_key = self._get_api_key()
            if not api_key:
                raise ValueError("Football-Data.org key not configured")
            code = self.COMPETITION_CODES.get(competition, competition)
            url = self._build_url("matches", competition=code)
            params = {"season": season} if season else {}
            headers = {"X-Auth-Token": api_key}
            response = self._make_request(url, params=params, headers=headers)
            response.raise_for_status()
            records = self.parse_response(response)
            saved = self._save_matches(records, competition)
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["successful"] += 1
            self.stats["records_collected"] += saved
            self._save_collection_log(f"fdorg_{competition}", "success", saved, "", elapsed)
            self._update_source_health(True, elapsed)
            return {"status": "success", "records": saved, "competition": competition, "duration_ms": elapsed}
        except Exception as e:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["failed"] += 1
            self._save_collection_log(f"fdorg_{competition}", "failed", 0, str(e), elapsed)
            self._update_source_health(False)
            return {"status": "error", "error": str(e), "competition": competition}

    def _get_api_key(self):
        import os
        return os.getenv("FOOTBALL_DATA_ORG_KEY") or self.config.get("api_key", "")

    def parse_response(self, response):
        data = self.json_parser.parse(response.content)
        if not data or "matches" not in data:
            return []
        records = []
        for m in data["matches"]:
            score = m.get("score", {}).get("fullTime", {})
            records.append({
                "match_id": m.get("id"),
                "match_date": (m.get("utcDate") or "")[:10],
                "match_time": (m.get("utcDate") or "")[11:16],
                "status": m.get("status", ""),
                "matchday": m.get("matchday"),
                "home_team": m.get("homeTeam", {}).get("name", ""),
                "away_team": m.get("awayTeam", {}).get("name", ""),
                "home_goals": score.get("home"),
                "away_goals": score.get("away"),
                "season": str((m.get("season") or {}).get("startDate", "")[:4]),
                "source_id": self.source_id,
            })
        return records

    def _save_matches(self, records, competition):
        if not records:
            return 0
        saved = 0
        for record in records:
            if not record.get("home_team") or not record.get("away_team"):
                continue
            for team_name in (record["home_team"], record["away_team"]):
                self.db.insert("teams", {
                    "name": team_name, "country": "", "source_id": self.source_id,
                    "source_team_id": f"fdorg_{team_name.replace(' ', '_')}", "is_active": 1,
                }, conflict_resolution="IGNORE")
            self.db.insert("matches", {
                "source_id": self.source_id, "source_match_id": str(record.get("match_id", "")),
                "season": record.get("season") or "unknown", "match_date": record.get("match_date", ""),
                "match_time": record.get("match_time", ""), "home_team_id": None, "away_team_id": None,
                "home_goals": record.get("home_goals"), "away_goals": record.get("away_goals"),
                "round": str(record.get("matchday", "")),
                "status": "finished" if record.get("home_goals") is not None else "scheduled",
                "is_processed": 0,
            }, conflict_resolution="IGNORE")
            saved += 1
        return saved

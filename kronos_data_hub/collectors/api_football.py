"""KRONOS_DATA_HUB - API-Football Collector (api-sports.io / v3.football.api-sports.io)"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from .base_collector import BaseCollector


class APIFootballCollector(BaseCollector):
    """
    API-Football (https://www.api-football.com/) icin collector.
    Kimlik dogrulama: header uzerinden 'x-apisports-key' (direkt api-sports.io
    aboneligi icin) kullanilir. RapidAPI uzerinden abone olunduysa bunun yerine
    'x-rapidapi-key' + 'x-rapidapi-host' gerekir; config['auth_mode'] ile
    secilebilir (varsayilan: "direct").
    """

    LEAGUE_IDS = {
        "premier_league": 39, "la_liga": 140, "bundesliga": 78,
        "serie_a": 135, "ligue_1": 61, "super_lig": 203,
        "champions_league": 2, "europa_league": 3,
    }

    def collect(self, league="premier_league", season="2025", **kwargs):
        start_time = datetime.now()
        self.stats["last_run"] = start_time.isoformat()
        try:
            api_key = self._get_api_key()
            if not api_key:
                raise ValueError("API-Football key not configured")
            league_id = self.LEAGUE_IDS.get(league, league)
            url = self._build_url("fixtures")
            params = {"league": league_id, "season": season}
            headers = self._auth_headers(api_key)
            response = self._make_request(url, params=params, headers=headers)
            response.raise_for_status()
            records = self.parse_response(response)
            saved = self._save_fixtures(records, league, season)
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["successful"] += 1
            self.stats["records_collected"] += saved
            self._save_collection_log(f"fixtures_{league}_{season}", "success", saved, "", elapsed)
            self._update_source_health(True, elapsed)
            return {"status": "success", "records": saved, "league": league, "season": season, "duration_ms": elapsed}
        except Exception as e:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["failed"] += 1
            self._save_collection_log(f"fixtures_{league}_{season}", "failed", 0, str(e), elapsed)
            self._update_source_health(False)
            return {"status": "error", "error": str(e), "league": league, "season": season}

    def _get_api_key(self):
        import os
        return os.getenv("API_FOOTBALL_KEY") or self.config.get("api_key", "")

    def _auth_headers(self, api_key):
        auth_mode = self.config.get("auth_mode", "direct")
        if auth_mode == "rapidapi":
            return {"x-rapidapi-key": api_key, "x-rapidapi-host": "api-football-v1.p.rapidapi.com"}
        return {"x-apisports-key": api_key}

    def parse_response(self, response):
        data = self.json_parser.parse(response.content)
        if not data or "response" not in data:
            return []
        records = []
        for item in data["response"]:
            fixture = item.get("fixture", {})
            teams = item.get("teams", {})
            goals = item.get("goals", {})
            league_info = item.get("league", {})
            records.append({
                "fixture_id": fixture.get("id"),
                "match_date": (fixture.get("date") or "")[:10],
                "match_time": (fixture.get("date") or "")[11:16],
                "status": fixture.get("status", {}).get("short", ""),
                "referee": fixture.get("referee"),
                "home_team": teams.get("home", {}).get("name", ""),
                "away_team": teams.get("away", {}).get("name", ""),
                "home_goals": goals.get("home"),
                "away_goals": goals.get("away"),
                "league_name": league_info.get("name", ""),
                "country": league_info.get("country", ""),
                "season": league_info.get("season", ""),
                "source_id": self.source_id,
            })
        return records

    def _save_fixtures(self, records, league, season):
        if not records:
            return 0
        saved = 0
        for record in records:
            if not record.get("home_team") or not record.get("away_team"):
                continue
            self.db.insert("leagues", {
                "name": record.get("league_name", league), "country": record.get("country", ""),
                "source_id": self.source_id, "source_league_id": str(record.get("fixture_id", "")),
                "season": str(record.get("season", season)), "is_active": 1,
            }, conflict_resolution="IGNORE")
            for team_name in (record["home_team"], record["away_team"]):
                self.db.insert("teams", {
                    "name": team_name, "country": record.get("country", ""),
                    "source_id": self.source_id,
                    "source_team_id": f"apifootball_{team_name.replace(' ', '_')}",
                    "is_active": 1,
                }, conflict_resolution="IGNORE")
            self.db.insert("matches", {
                "source_id": self.source_id, "source_match_id": str(record.get("fixture_id", "")),
                "season": str(record.get("season", season)), "match_date": record.get("match_date", ""),
                "match_time": record.get("match_time", ""), "home_team_id": None, "away_team_id": None,
                "home_goals": record.get("home_goals"), "away_goals": record.get("away_goals"),
                "referee": record.get("referee"),
                "status": "finished" if record.get("home_goals") is not None else "scheduled",
                "is_processed": 0,
            }, conflict_resolution="IGNORE")
            saved += 1
        return saved

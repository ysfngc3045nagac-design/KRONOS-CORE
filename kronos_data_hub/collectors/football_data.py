"""KRONOS_DATA_HUB - Football-Data.co.uk Collector"""
import io
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
from .base_collector import BaseCollector

class FootballDataCollector(BaseCollector):
    LEAGUE_CODES = {"E0": "Premier League", "E1": "Championship", "E2": "League One", "E3": "League Two",
        "EC": "Conference", "D1": "Bundesliga", "D2": "Bundesliga 2", "I1": "Serie A", "I2": "Serie B",
        "SP1": "La Liga", "SP2": "La Liga 2", "F1": "Ligue 1", "F2": "Ligue 2", "N1": "Eredivisie",
        "B1": "Jupiler Pro League", "P1": "Primeira Liga", "T1": "Super Lig", "G1": "Super League Greece"}

    def collect(self, season="2425", league="E0", **kwargs):
        start_time = datetime.now()
        self.stats["last_run"] = start_time.isoformat()
        try:
            url = self._build_url("fixtures", season=season, league=league)
            response = self._make_request(url)
            response.raise_for_status()
            records = self.parse_response(response)
            saved = self._save_matches(records, season, league)
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["successful"] += 1
            self.stats["records_collected"] += saved
            self._save_collection_log(f"matches_{season}_{league}", "success", saved, "", elapsed)
            self._update_source_health(True, elapsed)
            return {"status": "success", "records": saved, "season": season, "league": league, "duration_ms": elapsed}
        except Exception as e:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["failed"] += 1
            self._save_collection_log(f"matches_{season}_{league}", "failed", 0, str(e), elapsed)
            self._update_source_health(False)
            return {"status": "error", "error": str(e), "season": season, "league": league}

    def parse_response(self, response):
        content = response.content.decode("utf-8", errors="ignore")
        records = self.csv_parser.parse(content)
        field_map = {"div": "league_code", "date": "match_date", "time": "match_time", "hometeam": "home_team",
            "awayteam": "away_team", "fthg": "home_goals", "ftag": "away_goals", "ftr": "full_time_result",
            "hthg": "ht_home_goals", "htag": "ht_away_goals", "htr": "ht_result", "hs": "home_shots",
            "as": "away_shots", "hst": "home_shots_on_target", "ast": "away_shots_on_target",
            "hc": "home_corners", "ac": "away_corners", "hf": "home_fouls", "af": "away_fouls",
            "hy": "home_yellows", "ay": "away_yellows", "hr": "home_reds", "ar": "away_reds",
            "b365h": "bet365_home", "b365d": "bet365_draw", "b365a": "bet365_away",
            "bwh": "betway_home", "bwd": "betway_draw", "bwa": "betway_away",
            "psh": "pinnacle_home", "psd": "pinnacle_draw", "psa": "pinnacle_away"}
        normalized = []
        for record in records:
            mapped = {}
            for old_key, new_key in field_map.items():
                if old_key in record:
                    mapped[new_key] = record[old_key]
            if mapped.get("match_date"):
                try:
                    dt = datetime.strptime(mapped["match_date"], "%d/%m/%Y")
                    mapped["match_date"] = dt.strftime("%Y-%m-%d")
                except:
                    pass
            mapped["source_id"] = self.source_id
            mapped["collected_at"] = datetime.now().isoformat()
            normalized.append(mapped)
        return normalized

    def _save_matches(self, records, season, league):
        if not records:
            return 0
        self.db.insert("leagues", {"name": self.LEAGUE_CODES.get(league, league), "country": self._get_country(league),
            "source_id": self.source_id, "source_league_id": league, "season": season, "is_active": 1}, conflict_resolution="IGNORE")
        league_row = self.db.fetch_one("SELECT id FROM leagues WHERE source_league_id = ? AND season = ?", (league, season))
        league_id = league_row["id"] if league_row else None
        saved = 0
        for record in records:
            if not record.get("home_team") or not record.get("away_team"):
                continue
            home_team_id = self._get_or_create_team_id(record["home_team"], country=self._get_country(league),
                league_id=league_id, source_team_id=f"{league}_{record['home_team'].replace(' ', '_')}")
            away_team_id = self._get_or_create_team_id(record["away_team"], country=self._get_country(league),
                league_id=league_id, source_team_id=f"{league}_{record['away_team'].replace(' ', '_')}")
            self.db.insert("matches", {"source_id": self.source_id,
                "source_match_id": f"{season}_{league}_{record.get('match_date', '')}_{record['home_team']}_vs_{record['away_team']}",
                "league_id": league_id, "season": season, "match_date": record.get("match_date", ""),
                "match_time": record.get("match_time", ""), "home_team_id": home_team_id, "away_team_id": away_team_id,
                "home_goals": record.get("home_goals"), "away_goals": record.get("away_goals"),
                "status": "finished" if record.get("home_goals") is not None else "scheduled",
                "is_processed": 0}, conflict_resolution="IGNORE")
            saved += 1
        return saved

    def _get_country(self, league_code):
        country_map = {"E": "England", "D": "Germany", "I": "Italy", "SP": "Spain", "F": "France",
                        "N": "Netherlands", "B": "Belgium", "P": "Portugal", "T": "Turkey", "G": "Greece"}
        for prefix, country in country_map.items():
            if league_code.startswith(prefix):
                return country
        return "Unknown"

    def collect_all_leagues(self, season="2425"):
        results = {}
        for code in self.LEAGUE_CODES:
            self.logger.info(f"Collecting {code} for season {season}")
            results[code] = self.collect(season=season, league=code)
        return results

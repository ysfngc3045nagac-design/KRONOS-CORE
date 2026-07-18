"""KRONOS_DATA_HUB - FBref Collector"""
import re
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
from .base_collector import BaseCollector

class FBRefCollector(BaseCollector):
    LEAGUE_URLS = {"Premier League": "eng-Premier-League", "La Liga": "es-La-Liga", "Bundesliga": "de-Bundesliga",
                   "Serie A": "it-Serie-A", "Ligue 1": "fr-Ligue-1", "Champions League": "Champions-League"}

    def collect(self, league="Premier League", season="2024-2025", **kwargs):
        start_time = datetime.now()
        self.stats["last_run"] = start_time.isoformat()
        try:
            matches = self._collect_matches(league, season)
            detailed = kwargs.get("detailed", False)
            if detailed:
                for match in matches[:10]:
                    self._collect_match_details(match)
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["successful"] += 1
            self.stats["records_collected"] += len(matches)
            self._save_collection_log(f"fbref_{league}_{season}", "success", len(matches), "", elapsed)
            self._update_source_health(True, elapsed)
            return {"status": "success", "records": len(matches), "league": league, "season": season, "duration_ms": elapsed}
        except Exception as e:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["failed"] += 1
            self._save_collection_log(f"fbref_{league}_{season}", "failed", 0, str(e), elapsed)
            self._update_source_health(False)
            return {"status": "error", "error": str(e), "league": league, "season": season}

    def _collect_matches(self, league, season):
        league_slug = self.LEAGUE_URLS.get(league, league.replace(" ", "-"))
        url = f"https://fbref.com/en/comps/9/{league_slug}-Scores-and-Fixtures"
        response = self._make_request(url)
        self.html_parser.parse(response.text)
        matches = self.html_parser.extract_table("table.stats_table")
        normalized = []
        for match in matches:
            normalized.append({
                "match_date": match.get("date", ""), "match_time": match.get("time", ""),
                "round": match.get("round", ""), "day": match.get("day", ""), "venue": match.get("venue", ""),
                "home_team": match.get("home", ""), "away_team": match.get("away", ""),
                "home_goals": self._parse_goals(match.get("score", "")), "away_goals": None,
                "attendance": match.get("attendance"), "referee": match.get("referee", ""),
                "match_report_url": match.get("match_report", ""), "source_id": self.source_id,
                "collected_at": datetime.now().isoformat()
            })
        return normalized

    def _collect_match_details(self, match):
        report_url = match.get("match_report_url", "")
        if not report_url:
            return match
        match_id = self._extract_match_id(report_url)
        if not match_id:
            return match
        url = f"https://fbref.com/en/matches/{match_id}"
        try:
            response = self._make_request(url)
            self.html_parser.parse(response.text)
            stats_tables = self.html_parser.soup.find_all("table", {"id": re.compile("stats_.*")})
            match["statistics"] = []
            for table in stats_tables:
                team_type = "home" if "home" in table.get("id", "") else "away"
                stats = self.html_parser.extract_table(str(table))
                match["statistics"].append({"team_type": team_type, "stats": stats})
            scorebox = self.html_parser.select_one("div.scorebox")
            if scorebox:
                xg_elements = scorebox.select("div.score_xg")
                if len(xg_elements) >= 2:
                    match["home_xg"] = self._parse_float(xg_elements[0].get_text())
                    match["away_xg"] = self._parse_float(xg_elements[1].get_text())
        except Exception as e:
            self.logger.warning(f"Could not fetch match details: {e}")
        return match

    def _extract_match_id(self, url):
        match = re.search(r"/matches/([a-f0-9]+)", url)
        return match.group(1) if match else ""

    def _parse_goals(self, score_text):
        try:
            parts = score_text.split("\u2013")
            if len(parts) >= 1:
                return int(parts[0].strip())
        except:
            pass
        return None

    def _parse_float(self, text):
        try:
            return float(text.strip().replace(",", "."))
        except:
            return None

    def parse_response(self, response):
        self.html_parser.parse(response.text)
        return self.html_parser.extract_table("table")

    def collect_player_stats(self, player_id, season="2024-2025"):
        url = f"https://fbref.com/en/players/{player_id}/matchlogs/{season}"
        response = self._make_request(url)
        self.html_parser.parse(response.text)
        stats = self.html_parser.extract_table("table#matchlogs_all")
        return {"player_id": player_id, "season": season, "matches": stats, "source_id": self.source_id}

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
            # DUZELTME: matches listesi olusturuluyordu ama hicbir zaman
            # db.insert("matches", ...) ile kaydedilmiyordu; "success, N kayit"
            # loglaniyordu ama veritabanina TEK SATIR yazilmiyordu. Simdi
            # kaydediliyor ve gercek kaydedilen sayi raporlaniyor.
            saved = self._save_matches(matches, league, season)
            detailed = kwargs.get("detailed", False)
            saved_stats = 0
            if detailed:
                for match in matches[:10]:
                    detail = self._collect_match_details(match)
                    saved_stats += self._save_match_details(detail, league, season)
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["successful"] += 1
            self.stats["records_collected"] += saved
            self._save_collection_log(f"fbref_{league}_{season}", "success", saved, "", elapsed)
            self._update_source_health(True, elapsed)
            return {"status": "success", "records": saved, "match_statistics": saved_stats,
                    "league": league, "season": season, "duration_ms": elapsed}
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

    def _save_matches(self, matches, league, season):
        saved = 0
        for match in matches:
            if not match.get("home_team") or not match.get("away_team"):
                continue
            home_team_id = self._get_or_create_team_id(match["home_team"],
                source_team_id=f"fbref_{league}_{match['home_team'].replace(' ', '_')}")
            away_team_id = self._get_or_create_team_id(match["away_team"],
                source_team_id=f"fbref_{league}_{match['away_team'].replace(' ', '_')}")
            self.db.insert("matches", {
                "source_id": self.source_id,
                "source_match_id": f"fbref_{league}_{season}_{match.get('match_date', '')}_{match['home_team']}_vs_{match['away_team']}",
                "league_id": None, "season": season, "match_date": match.get("match_date", ""),
                "match_time": match.get("match_time", ""), "home_team_id": home_team_id, "away_team_id": away_team_id,
                "home_goals": match.get("home_goals"), "away_goals": match.get("away_goals"),
                "status": "finished" if match.get("home_goals") is not None else "scheduled",
                "venue": match.get("venue", ""), "referee": match.get("referee", ""),
                "attendance": match.get("attendance") or 0, "round": match.get("round", ""),
                "is_processed": 0}, conflict_resolution="IGNORE")
            saved += 1
        return saved

    def _save_match_details(self, match, league, season):
        """
        DUZELTME: detailed=True ile cekilen istatistik tablolari ve xG
        degerleri hicbir zaman match_statistics tablosuna yazilmiyordu -
        _collect_match_details sadece dict'e ekleyip donduruyordu. Simdi
        ilgili mac (varsa) bulunup her takim icin match_statistics satiri
        olusturuluyor.
        """
        if not match.get("statistics"):
            return 0
        row = self.db.fetch_one(
            "SELECT id FROM matches WHERE match_date = ? AND home_team_id IN "
            "(SELECT id FROM teams WHERE name = ?) AND away_team_id IN (SELECT id FROM teams WHERE name = ?)",
            (match.get("match_date", ""), match.get("home_team", ""), match.get("away_team", "")))
        if not row:
            return 0
        match_id = row["id"]
        saved = 0
        for stat_block in match.get("statistics", []):
            team_type = stat_block.get("team_type", "home")
            team_name = match.get("home_team") if team_type == "home" else match.get("away_team")
            team_row = self.db.fetch_one("SELECT id FROM teams WHERE name = ?", (team_name,))
            if not team_row:
                continue
            self.db.insert("match_statistics", {
                "match_id": match_id, "team_id": team_row["id"], "is_home": 1 if team_type == "home" else 0,
                "xg": match.get("home_xg") if team_type == "home" else match.get("away_xg", 0.0),
                "source_id": self.source_id,
            }, conflict_resolution="IGNORE")
            saved += 1
        return saved

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

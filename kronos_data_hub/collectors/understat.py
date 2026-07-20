"""KRONOS_DATA_HUB - Understat Collector"""
import re
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
from .base_collector import BaseCollector

class UnderstatCollector(BaseCollector):
    LEAGUE_CODES = {"EPL": "epl", "La Liga": "la_liga", "Bundesliga": "bundesliga", "Serie A": "serie_a",
                    "Ligue 1": "ligue_1", "RPL": "rfpl"}

    def collect(self, league="EPL", season="2024", **kwargs):
        start_time = datetime.now()
        self.stats["last_run"] = start_time.isoformat()
        try:
            league_code = self.LEAGUE_CODES.get(league, league.lower())
            url = f"https://understat.com/league/{league_code}/{season}"
            response = self._make_request(url)
            data = self._extract_js_data(response.text)
            matches = self._parse_matches(data.get("datesData", []))
            players = self._parse_players(data.get("playersData", []))
            saved_matches = self._save_matches(matches, league, season)
            saved_players = self._save_players(players)
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["successful"] += 1
            self.stats["records_collected"] += saved_matches + saved_players
            self._save_collection_log(f"understat_{league}_{season}", "success", saved_matches + saved_players, "", elapsed)
            self._update_source_health(True, elapsed)
            return {"status": "success", "matches": saved_matches, "players": saved_players, "league": league, "season": season, "duration_ms": elapsed}
        except Exception as e:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["failed"] += 1
            self._save_collection_log(f"understat_{league}_{season}", "failed", 0, str(e), elapsed)
            self._update_source_health(False)
            return {"status": "error", "error": str(e), "league": league, "season": season}

    def _extract_js_data(self, html):
        data = {}
        patterns = {"datesData": r"datesData\s*=\s*JSON\.parse\('([^']+)'\)",
                    "playersData": r"playersData\s*=\s*JSON\.parse\('([^']+)'\)",
                    "teamsData": r"teamsData\s*=\s*JSON\.parse\('([^']+)'\)"}
        for key, pattern in patterns.items():
            match = re.search(pattern, html)
            if match:
                try:
                    json_str = match.group(1).encode().decode("unicode_escape")
                    data[key] = json.loads(json_str)
                except Exception as e:
                    self.logger.warning(f"Could not parse {key}: {e}")
                    data[key] = []
        return data

    def _parse_matches(self, dates_data):
        matches = []
        for date_entry in dates_data:
            for match in date_entry.get("matches", []):
                dt = match.get("datetime", "")
                matches.append({
                    "match_id": match.get("id"),
                    "match_date": dt.split(" ")[0] if dt else "",
                    "match_time": dt.split(" ")[1] if dt and " " in dt else "",
                    "home_team": match.get("h", {}).get("title", ""), "away_team": match.get("a", {}).get("title", ""),
                    "home_goals": match.get("goals", {}).get("h"), "away_goals": match.get("goals", {}).get("a"),
                    "home_xg": match.get("xG", {}).get("h"), "away_xg": match.get("xG", {}).get("a"),
                    "forecast": match.get("forecast", {}), "is_finished": match.get("isResult", False),
                    "source_id": self.source_id, "collected_at": datetime.now().isoformat()
                })
        return matches

    def _parse_players(self, players_data):
        players = []
        for player in players_data:
            players.append({
                "player_id": player.get("id"), "name": player.get("player_name", ""), "team": player.get("team_title", ""),
                "position": player.get("position", ""), "games": player.get("games", 0), "time": player.get("time", 0),
                "goals": player.get("goals", 0), "xG": player.get("xG", 0), "assists": player.get("assists", 0),
                "xA": player.get("xA", 0), "shots": player.get("shots", 0), "key_passes": player.get("key_passes", 0),
                "yellow_cards": player.get("yellow_cards", 0), "red_cards": player.get("red_cards", 0),
                "npg": player.get("npg", 0), "npxG": player.get("npxG", 0), "xGChain": player.get("xGChain", 0),
                "xGBuildup": player.get("xGBuildup", 0), "source_id": self.source_id
            })
        return players

    def _save_matches(self, matches, league, season):
        saved = 0
        for match in matches:
            if not match.get("home_team") or not match.get("away_team"):
                continue
            # DUZELTME: home_team_id/away_team_id hep None yaziliyordu, bu yuzden
            # understat maclari hicbir takima baglanamiyordu. Diger collector'lerle
            # ayni desen (_get_or_create_team_id) kullanilarak baglanti kuruluyor.
            home_team_id = self._get_or_create_team_id(match["home_team"],
                source_team_id=f"understat_{match['home_team'].replace(' ', '_')}")
            away_team_id = self._get_or_create_team_id(match["away_team"],
                source_team_id=f"understat_{match['away_team'].replace(' ', '_')}")
            self.db.insert("matches", {"source_id": self.source_id, "source_match_id": str(match.get("match_id", "")),
                "league_id": None, "season": season, "match_date": match.get("match_date", ""),
                "match_time": match.get("match_time", ""), "home_team_id": home_team_id, "away_team_id": away_team_id,
                "home_goals": match.get("home_goals"), "away_goals": match.get("away_goals"),
                "status": "finished" if match.get("is_finished") else "scheduled", "is_processed": 0}, conflict_resolution="IGNORE")
            saved += 1
        return saved

    def _save_players(self, players):
        """
        DUZELTME: _parse_players() oyunculari cekiyordu ama hicbir yerde
        db.insert("players", ...) cagrilmiyordu - sonuc dashboard'da hep
        players=0 gorunuyordu. Simdi her oyuncu, mumkunse takimina
        baglanarak (team_id) players tablosuna yaziliyor.
        """
        saved = 0
        for player in players:
            name = player.get("name", "")
            if not name:
                continue
            team_id = None
            team_name = player.get("team", "")
            if team_name:
                team_id = self._get_or_create_team_id(team_name,
                    source_team_id=f"understat_{team_name.replace(' ', '_')}")
            self._get_or_create_player_id(name, team_id=team_id, position=player.get("position", ""),
                source_player_id=f"understat_{player.get('player_id', name.replace(' ', '_'))}")
            saved += 1
        return saved

    def collect_match_shots(self, match_id):
        url = f"https://understat.com/match/{match_id}"
        response = self._make_request(url)
        data = self._extract_js_data(response.text)
        shots_data = data.get("shotsData", {})
        shots = []
        for team_type, team_shots in shots_data.items():
            for shot in team_shots:
                shots.append({"match_id": match_id, "team_type": team_type, "minute": shot.get("minute"),
                    "player": shot.get("player"), "xG": shot.get("xG"), "shot_type": shot.get("shotType"),
                    "result": shot.get("result"), "x": shot.get("X"), "y": shot.get("Y"), "source_id": self.source_id})
        return shots

    def parse_response(self, response):
        data = self._extract_js_data(response.text)
        return self._parse_matches(data.get("datesData", []))

"""KRONOS_DATA_HUB - Odds API Collector"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
from .base_collector import BaseCollector

class OddsCollector(BaseCollector):
    SPORT_KEYS = {"soccer_epl": "EPL", "soccer_spain_la_liga": "La Liga", "soccer_germany_bundesliga": "Bundesliga",
        "soccer_italy_serie_a": "Serie A", "soccer_france_ligue_one": "Ligue 1",
        "soccer_uefa_champs_league": "Champions League", "soccer_uefa_europa_league": "Europa League"}

    def collect(self, sport="soccer_epl", regions="eu,uk", markets="h2h,totals", **kwargs):
        start_time = datetime.now()
        self.stats["last_run"] = start_time.isoformat()
        try:
            api_key = self._get_api_key()
            if not api_key:
                raise ValueError("Odds API key not configured")
            url = self._build_url("odds", sport=sport)
            params = {"apiKey": api_key, "regions": regions, "markets": markets, "oddsFormat": "decimal", "dateFormat": "iso"}
            response = self._make_request(url, params=params)
            response.raise_for_status()
            records = self.parse_response(response)
            saved = self._save_odds(records, sport)
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["successful"] += 1
            self.stats["records_collected"] += saved
            self._save_collection_log(f"odds_{sport}", "success", saved, "", elapsed)
            self._update_source_health(True, elapsed)
            return {"status": "success", "records": saved, "sport": sport, "markets": markets.split(","), "duration_ms": elapsed}
        except Exception as e:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["failed"] += 1
            self._save_collection_log(f"odds_{sport}", "failed", 0, str(e), elapsed)
            self._update_source_health(False)
            return {"status": "error", "error": str(e), "sport": sport}

    def _get_api_key(self):
        import os
        return os.getenv("ODDS_API_KEY") or self.config.get("api_key", "")

    def parse_response(self, response):
        data = self.json_parser.parse(response.content)
        if not data or not isinstance(data, list):
            return []
        records = []
        for event in data:
            event_id = event.get("id", "")
            home_team = event.get("home_team", "")
            away_team = event.get("away_team", "")
            commence_time = event.get("commence_time", "")
            for bookmaker in event.get("bookmakers", []):
                bookmaker_name = bookmaker.get("title", "")
                for market in bookmaker.get("markets", []):
                    market_key = market.get("key", "")
                    if market_key == "h2h":
                        outcomes = market.get("outcomes", [])
                        home_odds = draw_odds = away_odds = 0.0
                        for outcome in outcomes:
                            name = outcome.get("name", "")
                            price = outcome.get("price", 0)
                            if name == home_team:
                                home_odds = price
                            elif name == away_team:
                                away_odds = price
                            elif name in ("Draw", "Tie"):
                                draw_odds = price
                        records.append({"event_id": event_id, "home_team": home_team, "away_team": away_team,
                            "commence_time": commence_time, "bookmaker": bookmaker_name, "market": "1X2",
                            "home_odds": home_odds, "draw_odds": draw_odds, "away_odds": away_odds,
                            "timestamp": datetime.now().isoformat(), "source_id": self.source_id})
                    elif market_key == "totals":
                        for outcome in market.get("outcomes", []):
                            records.append({"event_id": event_id, "home_team": home_team, "away_team": away_team,
                                "commence_time": commence_time, "bookmaker": bookmaker_name,
                                "market": f"totals_{outcome.get('point', 0)}",
                                "over_odds": outcome.get("price", 0) if outcome.get("name") == "Over" else 0,
                                "under_odds": outcome.get("price", 0) if outcome.get("name") == "Under" else 0,
                                "handicap": outcome.get("point", 0), "timestamp": datetime.now().isoformat(),
                                "source_id": self.source_id})
        return records

    def _save_odds(self, records, sport):
        saved = 0
        for record in records:
            match_id = self._find_or_create_match(record)
            self.db.insert("odds", {"match_id": match_id, "source_id": self.source_id, "bookmaker": record["bookmaker"],
                "market": record["market"], "home_odds": record.get("home_odds", 0), "draw_odds": record.get("draw_odds", 0),
                "away_odds": record.get("away_odds", 0), "over_odds": record.get("over_odds", 0),
                "under_odds": record.get("under_odds", 0), "handicap": record.get("handicap", 0),
                "timestamp": record["timestamp"], "is_live": 0}, conflict_resolution="IGNORE")
            saved += 1
        return saved

    def _find_or_create_match(self, record):
        home = record.get("home_team", "")
        away = record.get("away_team", "")
        date = record.get("commence_time", "")[:10]
        existing = self.db.fetch_one(
            """SELECT id FROM matches WHERE (home_team_id IN (SELECT id FROM teams WHERE name LIKE ?)
               OR away_team_id IN (SELECT id FROM teams WHERE name LIKE ?)) AND match_date = ? LIMIT 1""",
            (f"%{home}%", f"%{away}%", date))
        if existing:
            return existing["id"]
        return self.db.insert("matches", {"source_id": self.source_id, "source_match_id": record.get("event_id", ""),
            "season": date[:4] if date else "", "match_date": date,
            "match_time": record.get("commence_time", "")[11:16] if len(record.get("commence_time", "")) > 10 else "",
            "status": "scheduled", "is_processed": 0})

    def collect_all_sports(self):
        results = {}
        for sport_key in self.SPORT_KEYS:
            self.logger.info(f"Collecting odds for {sport_key}")
            results[sport_key] = self.collect(sport=sport_key)
        return results

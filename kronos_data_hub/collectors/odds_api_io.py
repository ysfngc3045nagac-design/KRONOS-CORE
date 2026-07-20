"""
KRONOS_DATA_HUB - Odds-API.io Collector (api.odds-api.io/v3)

Kullanicinin gonderdigi ornek kod baz alinarak yazildi:
    GET https://api.odds-api.io/v3/odds?apiKey=...&eventId=...&bookmakers=...&region=...
Kimlik dogrulama query param uzerinden ('apiKey'). the-odds-api.com,
theoddsapi.com ve API-Football'dan AYRI, dorduncu bir servis.

DIKKAT: Sadece istek (request) ornegi elimizde var, DONEN JSON'un tam semasi
(alan adlari) dokumantasyonla dogrulanmadi. parse_response() makul/genel bir
odds JSON yapisi varsayarak yazildi (event/bookmakers/outcomes ic ice yapisi,
diger odds servislerinde yaygin olan sema). Ilk canli calistirmadan sonra
gercek yanit ile karsilastirilip gerekirse alan adlari duzeltilmelidir.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from .base_collector import BaseCollector


class OddsAPIIOCollector(BaseCollector):

    def collect(self, event_id=None, bookmakers="Bet365,DraftKings,Betfair", region="eu", **kwargs):
        start_time = datetime.now()
        self.stats["last_run"] = start_time.isoformat()
        try:
            api_key = self._get_api_key()
            if not api_key:
                raise ValueError("odds-api.io key not configured")
            url = self._build_url("odds")
            params = {"apiKey": api_key, "bookmakers": bookmakers, "region": region}
            if event_id:
                params["eventId"] = event_id
            response = self._make_request(url, params=params)
            response.raise_for_status()
            records = self.parse_response(response)
            saved = self._save_odds(records)
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["successful"] += 1
            self.stats["records_collected"] += saved
            self._save_collection_log("odds_api_io", "success", saved, "", elapsed)
            self._update_source_health(True, elapsed)
            return {"status": "success", "records": saved, "duration_ms": elapsed}
        except Exception as e:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["failed"] += 1
            self._save_collection_log("odds_api_io", "failed", 0, str(e), elapsed)
            self._update_source_health(False)
            return {"status": "error", "error": str(e)}

    def _get_api_key(self):
        import os
        return os.getenv("ODDS_API_IO_KEY") or self.config.get("api_key", "")

    def parse_response(self, response):
        # NOT: gercek sema dogrulanmadi, bkz. modul basi uyarisi.
        data = self.json_parser.parse(response.content)
        if not data:
            return []
        events = data if isinstance(data, list) else data.get("data", data.get("events", []))
        if not isinstance(events, list):
            return []
        records = []
        for event in events:
            home_team = event.get("homeTeam") or event.get("home_team", "")
            away_team = event.get("awayTeam") or event.get("away_team", "")
            commence_time = event.get("startTime") or event.get("commence_time", "")
            for bm in event.get("bookmakers", []):
                home_odds = draw_odds = away_odds = 0.0
                outcomes = bm.get("odds") or bm.get("outcomes", [])
                if isinstance(outcomes, dict):
                    home_odds = outcomes.get("home", 0.0)
                    draw_odds = outcomes.get("draw", 0.0)
                    away_odds = outcomes.get("away", 0.0)
                elif isinstance(outcomes, list):
                    for o in outcomes:
                        name, price = o.get("name", ""), o.get("price", 0.0)
                        if name == home_team:
                            home_odds = price
                        elif name == away_team:
                            away_odds = price
                        elif name.lower() in ("draw", "tie"):
                            draw_odds = price
                records.append({
                    "event_id": event.get("id", ""), "home_team": home_team, "away_team": away_team,
                    "commence_time": commence_time, "bookmaker": bm.get("name", bm.get("bookmaker", "")),
                    "home_odds": home_odds, "draw_odds": draw_odds, "away_odds": away_odds,
                    "timestamp": datetime.now().isoformat(), "source_id": self.source_id,
                })
        return records

    def _save_odds(self, records):
        saved = 0
        for record in records:
            match_id = self._find_or_create_match(record)
            self.db.insert("odds", {
                "match_id": match_id, "source_id": self.source_id, "bookmaker": record["bookmaker"],
                "market": "1X2", "home_odds": record.get("home_odds", 0), "draw_odds": record.get("draw_odds", 0),
                "away_odds": record.get("away_odds", 0), "timestamp": record["timestamp"], "is_live": 0,
            }, conflict_resolution="IGNORE")
            saved += 1
        return saved

    def _find_or_create_match(self, record):
        home, away = record.get("home_team", ""), record.get("away_team", "")
        date = (record.get("commence_time") or "")[:10]
        existing = self.db.fetch_one(
            """SELECT id FROM matches WHERE (home_team_id IN (SELECT id FROM teams WHERE name LIKE ?)
               OR away_team_id IN (SELECT id FROM teams WHERE name LIKE ?)) AND match_date = ? LIMIT 1""",
            (f"%{home}%", f"%{away}%", date))
        if existing:
            return existing["id"]
        home_team_id = self._get_or_create_team_id(home)
        away_team_id = self._get_or_create_team_id(away)
        return self.db.insert("matches", {
            "source_id": self.source_id, "source_match_id": record.get("event_id", ""),
            "season": date[:4] if date else "unknown", "match_date": date,
            "match_time": (record.get("commence_time") or "")[11:16],
            "home_team_id": home_team_id, "away_team_id": away_team_id,
            "status": "scheduled", "is_processed": 0,
        })

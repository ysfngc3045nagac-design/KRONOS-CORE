"""
KRONOS_DATA_HUB - Collector testleri.

Ag baglantisi kullanilmiyor (sandbox/CI ortaminda internet olmayabilir).
Bunun yerine collector'larin parse_response() metodlarini sahte (mock)
bir HTTP yaniti ile test ediyoruz - gercek collect() akisinin sadece
"veriyi dogru sekilde satirlara/alanlara donusturme" kismini dogruluyoruz.
"""

import unittest
from types import SimpleNamespace

from database.sqlite_manager import SQLiteManager
from database.cache import CacheManager
from core.rate_limiter import RateLimiter
from core.retry_manager import RetryManager
from collectors.football_data import FootballDataCollector
from collectors.base_collector import BaseCollector


def _build_collector(collector_cls, source_id, config):
    """Ag gerektirmeyen, gercek (ama gecici) bagimliliklarla bir collector kurar."""
    SQLiteManager._instance = None
    db = SQLiteManager(":memory:")
    cache = CacheManager(db, memory_size=100, default_ttl_seconds=60)
    rate_limiter = RateLimiter()
    retry_manager = RetryManager()
    return collector_cls(
        source_id=source_id, config=config, db=db,
        rate_limiter=rate_limiter, retry_manager=retry_manager, cache=cache,
    )


class TestFootballDataCollector(unittest.TestCase):

    def setUp(self):
        config = {
            "base_url": "https://www.football-data.co.uk/mmz4281",
            "endpoints": {"fixtures": "/{season}/{league}.csv"},
            "timeout": 30,
        }
        self.collector = _build_collector(FootballDataCollector, "football_data", config)

    def test_parse_response_maps_known_columns(self):
        csv_body = (
            "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n"
            "E0,15/07/2026,Arsenal,Chelsea,2,1,H\n"
        ).encode("utf-8")

        fake_response = SimpleNamespace(content=csv_body)

        records = self.collector.parse_response(fake_response)

        self.assertEqual(len(records), 1)
        row = records[0]
        self.assertEqual(row["home_team"], "Arsenal")
        self.assertEqual(row["away_team"], "Chelsea")
        # tarih donusumu dd/mm/yyyy -> yyyy-mm-dd calismis olmali
        self.assertEqual(row["match_date"], "2026-07-15")
        self.assertEqual(row["source_id"], "football_data")

    def test_parse_response_empty_csv_returns_empty_list(self):
        fake_response = SimpleNamespace(content=b"Div,Date,HomeTeam,AwayTeam\n")
        records = self.collector.parse_response(fake_response)
        self.assertEqual(records, [])


class TestBaseCollectorHelpers(unittest.TestCase):
    """BaseCollector soyut oldugu icin FootballDataCollector uzerinden
    ortak yardimci metodlari (._build_url, .get_stats) test ediyoruz."""

    def setUp(self):
        config = {
            "base_url": "https://example.com/api",
            "endpoints": {"fixtures": "/{season}/{league}.csv"},
        }
        self.collector = _build_collector(FootballDataCollector, "football_data", config)

    def test_build_url_substitutes_params(self):
        url = self.collector._build_url("fixtures", season="2425", league="E0")
        self.assertEqual(url, "https://example.com/api/2425/E0.csv")

    def test_build_url_missing_param_leaves_placeholder(self):
        # KeyError yakalanip oldugu gibi birakiliyor - crash etmemeli
        url = self.collector._build_url("fixtures", season="2425")
        self.assertIn("{league}", url)

    def test_get_stats_initial_state(self):
        stats = self.collector.get_stats()
        self.assertEqual(stats["requests"], 0)
        self.assertEqual(stats["source_id"], "football_data")


if __name__ == "__main__":
    unittest.main()

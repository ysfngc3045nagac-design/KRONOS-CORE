"""KRONOS_DATA_HUB - AI modul testleri (veritabani gerektirmeyenler icin sqlite :memory:)."""

import unittest
import sqlite3

from ai.data_cleaner import DataCleaner
from database.sqlite_manager import SQLiteManager


class TestDataCleaner(unittest.TestCase):

    def setUp(self):
        self.cleaner = DataCleaner()

    def test_clean_team_name_removes_fc_suffix(self):
        self.assertEqual(self.cleaner._clean_team_name("Arsenal FC"), "Arsenal")

    def test_clean_odds_rejects_out_of_range(self):
        self.assertIsNone(self.cleaner._clean_odds("0.5"))   # 1.01 altinda gecersiz
        self.assertIsNone(self.cleaner._clean_odds("5000"))  # 1000 ustunde gecersiz
        self.assertEqual(self.cleaner._clean_odds("2,50"), 2.5)  # virgullu ondalik

    def test_clean_date_multiple_formats(self):
        self.assertEqual(self.cleaner._clean_date("15/07/2026"), "2026-07-15")
        self.assertEqual(self.cleaner._clean_date("2026-07-15"), "2026-07-15")

    def test_remove_duplicates(self):
        records = [
            {"home": "A", "away": "B", "date": "2026-01-01"},
            {"home": "A", "away": "B", "date": "2026-01-01"},  # duplike
            {"home": "C", "away": "D", "date": "2026-01-01"},
        ]
        unique = self.cleaner.remove_duplicates(records, key_fields=["home", "away", "date"])
        self.assertEqual(len(unique), 2)

    def test_validate_required_fields_detects_missing(self):
        missing = self.cleaner.validate_required_fields(
            {"home": "A", "away": None}, required=["home", "away", "date"]
        )
        self.assertIn("away", missing)
        self.assertIn("date", missing)
        self.assertNotIn("home", missing)


class TestSQLiteManagerBasics(unittest.TestCase):
    """AI modulleri (confidence, anomaly_detector, duplicate_detector) hepsi
    SQLiteManager uzerinden calisiyor - burada temel CRUD davranisini
    dogruluyoruz, boylece uzerine kurulan AI mantigi guvenilir bir zemine
    dayanmis oluyor."""

    def setUp(self):
        SQLiteManager._instance = None
        self.db = SQLiteManager(":memory:")

    def test_insert_and_fetch(self):
        row_id = self.db.insert("teams", {"name": "Test Takim", "country": "TR", "source_id": "test"})
        self.assertIsNotNone(row_id)
        row = self.db.fetch_one("SELECT * FROM teams WHERE id = ?", (row_id,))
        self.assertEqual(row["name"], "Test Takim")

    def test_fetch_scalar_on_empty_table(self):
        count = self.db.fetch_scalar("SELECT COUNT(*) FROM teams")
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()

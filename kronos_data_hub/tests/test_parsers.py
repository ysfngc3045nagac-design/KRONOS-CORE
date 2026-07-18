"""
KRONOS_DATA_HUB - Parser testleri.

NOT: main.py --mode test bu modulu ariyordu ama daha once hic
yazilmamisti (tests/ klasoru bostu, sadece log uyarisi verip
sessizce "0 test calisti / basarili" gibi yaniltici bir sonuc
donuyordu). Bu dosya gercek, ag baglantisi gerektirmeyen testler
icerir.
"""

import unittest

from parsers.csv_parser import CSVParser
from parsers.json_parser import JSONParser


class TestCSVParser(unittest.TestCase):

    def setUp(self):
        self.parser = CSVParser()

    def test_parse_with_header(self):
        data = "Home Team,Away Team,Score\nFenerbahce,Galatasaray,2-1\n"
        rows = self.parser.parse(data)
        self.assertEqual(len(rows), 1)
        # basliklar kucuk harfe + alt cizgiye donusturulmus olmali
        self.assertIn("home_team", rows[0])
        self.assertEqual(rows[0]["home_team"], "Fenerbahce")

    def test_empty_and_na_values_become_none(self):
        data = "team,score\nA,NA\nB,\n"
        rows = self.parser.parse(data)
        self.assertIsNone(rows[0]["score"])
        self.assertIsNone(rows[1]["score"])

    def test_numeric_conversion(self):
        data = "team,goals\nA,3\n"
        rows = self.parser.parse(data)
        self.assertEqual(rows[0]["goals"], 3)
        self.assertIsInstance(rows[0]["goals"], int)

    def test_malformed_input_does_not_crash(self):
        # gecersiz bir kodlama/format verilse bile exception firlatmamali,
        # bos liste donup hatayi self.errors'a kaydetmeli
        result = self.parser.parse(b"\xff\xfe\x00\x01", encoding="ascii")
        self.assertEqual(result, [])
        self.assertTrue(len(self.parser.errors) > 0)


class TestJSONParser(unittest.TestCase):

    def setUp(self):
        self.parser = JSONParser()

    def test_parse_valid_json(self):
        result = self.parser.parse('{"home": "A", "away": "B", "score": [2, 1]}')
        self.assertEqual(result["home"], "A")
        self.assertEqual(result["score"], [2, 1])

    def test_parse_invalid_json_returns_none_or_empty(self):
        result = self.parser.parse("{gecersiz json")
        self.assertIn(result, (None, {}, []))


if __name__ == "__main__":
    unittest.main()

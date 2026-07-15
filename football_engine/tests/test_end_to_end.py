"""
Uctan uca temel testler. Calistirmak icin (kronos/ klasorunun icinden):

    python3 -m pytest tests/ -v

veya pytest yoksa:

    python3 tests/test_end_to_end.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest


class TestEndToEnd(unittest.TestCase):

    def test_kronos_application_analyze(self):
        from football_engine.core.app import KronosApplication

        app = KronosApplication()

        match = {
            "id": "test-e2e-1",
            "home_elo": 1650, "away_elo": 1500,
            "xg": 1.8, "xga": 0.9,
            "scored": [2, 1, 3], "conceded": [0, 1, 1],
            "recent_results": [{"home_goals": 2, "away_goals": 1, "home": True}],
            "odds": {"home": 1.8, "draw": 3.6, "away": 4.2},
        }

        report = app.analyze(match, save=False)

        self.assertIn("overall_score", report)
        self.assertIn("decision", report)
        self.assertIn("confidence", report)
        self.assertGreater(report["confidence"], 0)

    def test_form_engine_respects_home_flag(self):
        """Regresyon testi: FormEngine artik home/away'i dogru ayirt ediyor."""
        from football_engine.core.analysis.engines.form_engine import FormEngine, MatchResult

        engine = FormEngine()

        # Takim deplasmanda 2-1 kazandi (away_goals > home_goals, home=False)
        away_win = [MatchResult(home_goals=1, away_goals=2, home=False)]
        score = engine.calculate(away_win)

        self.assertEqual(score, 100.0)  # tam galibiyet -> 100

    def test_goal_engine_empty_conceded_no_crash(self):
        """Regresyon testi: conceded bos oldugunda ZeroDivisionError verilmemeli."""
        from football_engine.core.analysis.engines.goal_engine import GoalEngine

        engine = GoalEngine()
        result = engine.analyze(scored=[1, 2], conceded=[])

        self.assertEqual(result, {"attack": 0, "defense": 0})

    def test_streak_engine_empty_no_crash(self):
        from football_engine.core.analysis.engines.streak_engine import StreakEngine

        engine = StreakEngine()
        result = engine.calculate([])

        self.assertEqual(result["form"], 0)

    def test_generate_uuid_tool_valid_syntax(self):
        """Regresyon testi: eski surumde SyntaxError veren generate_uuid duzeldi."""
        from football_engine.core.tools.uuid_tools import generate_uuid
        import uuid as uuid_module

        value = generate_uuid()
        parsed = uuid_module.UUID(value)  # exception atmazsa gecerli UUID
        self.assertEqual(str(parsed), value)

    def test_write_csv_handles_varying_fieldnames(self):
        """Regresyon testi: farkli key'lere sahip satirlar artik ValueError vermiyor."""
        import tempfile
        from football_engine.core.tools.csv_tools import write_csv, read_csv

        rows = [{"a": 1, "b": 2}, {"a": 3, "c": 4}]

        with tempfile.TemporaryDirectory() as tmp:
            path = f"{tmp}/test.csv"
            result = write_csv(path, rows)
            self.assertEqual(result, "OK")

            loaded = read_csv(path)
            self.assertEqual(len(loaded), 2)


if __name__ == "__main__":
    unittest.main()

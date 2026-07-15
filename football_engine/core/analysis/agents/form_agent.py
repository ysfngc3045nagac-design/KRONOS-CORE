"""
Form analizi yapan ajan.

NOT: Orijinal FormAgent sabit deger donduren bir mock'tu (score: 82 hep ayni).
Artik gercek FormEngine'i kullanip match["recent_results"] listesinden
hesapliyor (her eleman {"home_goals", "away_goals", "home": bool}).
Veri yoksa notr (50) skor doner, "yetersiz veri" bilgisiyle.
"""

from football_engine.core.analysis.agent import Agent
from football_engine.core.analysis.engines.form_engine import FormEngine, MatchResult


class FormAgent(Agent):

    def __init__(self):
        super().__init__("form")
        self.engine = FormEngine()

    def analyze(self, match: dict) -> dict:

        raw_results = match.get("recent_results", [])

        if not raw_results:
            return {
                "score": 50,
                "prediction": None,
                "confidence": 20,
                "details": {"reason": "Son mac verisi yok, notr skor."},
            }

        parsed = [
            MatchResult(
                home_goals=r["home_goals"],
                away_goals=r["away_goals"],
                home=r.get("home", True),
            )
            for r in raw_results
        ]

        score = self.engine.calculate(parsed)

        prediction = "HOME" if score >= 55 else ("AWAY" if score <= 45 else "DRAW")

        return {
            "score": score,
            "prediction": prediction,
            "confidence": min(90, 40 + len(parsed) * 8),
            "details": {"matches_used": len(parsed)},
        }

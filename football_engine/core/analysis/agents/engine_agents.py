"""
core/analysis/engines/*.py icindeki hesaplama motorlarini standart Agent
arayuzune (analyze(match) -> {score, prediction, confidence, details})
saran adapter ajanlar.

Her ajan, match sozlugunden ihtiyac duydugu alanlari .get() ile okur ve
veri yoksa makul bir varsayilanla notr sonuc uretir (0'a bolme / KeyError
riskini ortadan kaldirir).
"""

from football_engine.core.analysis.agent import Agent
from football_engine.core.analysis.engines import (
    GoalEngine, XGEngine, EloEngine, InjuryEngine, HomeAdvantageEngine,
    FixtureEngine, FatigueEngine, WeatherEngine, MotivationEngine,
    RefereeEngine, OddsEngine, StreakEngine, PressureEngine,
)


class GoalAgent(Agent):

    def __init__(self):
        super().__init__("goal")
        self.engine = GoalEngine()

    def analyze(self, match: dict) -> dict:
        result = self.engine.analyze(
            match.get("scored", []),
            match.get("conceded", []),
        )
        score = round((result["attack"] + result["defense"]) / 2, 2)
        return {"score": score, "prediction": None, "confidence": 60, "details": result}


class XGAgent(Agent):

    def __init__(self):
        super().__init__("xg")
        self.engine = XGEngine()

    def analyze(self, match: dict) -> dict:
        result = self.engine.evaluate(match.get("xg", 1.2), match.get("xga", 1.2))
        score = round((result["attack"] + result["defense"]) / 2, 2)
        return {"score": score, "prediction": None, "confidence": 65, "details": result}


class EloAgent(Agent):

    def __init__(self):
        super().__init__("elo")
        self.engine = EloEngine()

    def analyze(self, match: dict) -> dict:
        probs = self.engine.probability(
            match.get("home_elo", 1500), match.get("away_elo", 1500)
        )
        prediction = max(probs, key=probs.get)
        return {
            "score": probs["home"],
            "prediction": prediction.upper() if prediction != "draw" else "DRAW",
            "confidence": 70,
            "details": probs,
        }


class InjuryAgent(Agent):

    def __init__(self):
        super().__init__("injury")
        self.engine = InjuryEngine()

    def analyze(self, match: dict) -> dict:
        score = self.engine.calculate(
            match.get("injured_players", 0), match.get("key_players_injured", 0)
        )
        return {"score": score, "prediction": None, "confidence": 55, "details": {}}


class HomeAdvantageAgent(Agent):

    def __init__(self):
        super().__init__("home_advantage")
        self.engine = HomeAdvantageEngine()

    def analyze(self, match: dict) -> dict:
        score = self.engine.calculate(
            match.get("home_win_rate", 45.0),
            match.get("attendance_rate", 80.0),
            match.get("away_travel_km", 0.0),
        )
        return {"score": score, "prediction": "HOME" if score > 55 else None, "confidence": 50, "details": {}}


class FixtureAgent(Agent):

    def __init__(self):
        super().__init__("fixture")
        self.engine = FixtureEngine()

    def analyze(self, match: dict) -> dict:
        score = self.engine.calculate(
            match.get("matches_last_7_days", 0), match.get("matches_last_30_days", 0)
        )
        return {"score": score, "prediction": None, "confidence": 55, "details": {}}


class FatigueAgent(Agent):

    def __init__(self):
        super().__init__("fatigue")
        self.engine = FatigueEngine()

    def analyze(self, match: dict) -> dict:
        score = self.engine.calculate(match.get("travel_km", 0), match.get("rest_days", 5))
        return {"score": score, "prediction": None, "confidence": 50, "details": {}}


class WeatherAgent(Agent):

    def __init__(self):
        super().__init__("weather")
        self.engine = WeatherEngine()

    def analyze(self, match: dict) -> dict:
        score = self.engine.calculate(
            match.get("temperature", 18.0), match.get("wind_speed", 10.0), match.get("rain", False)
        )
        return {"score": score, "prediction": None, "confidence": 40, "details": {}}


class MotivationAgent(Agent):

    def __init__(self):
        super().__init__("motivation")
        self.engine = MotivationEngine()

    def analyze(self, match: dict) -> dict:
        score = self.engine.calculate(
            match.get("league_position", 10), match.get("title_race", False), match.get("relegation", False)
        )
        return {"score": score, "prediction": None, "confidence": 55, "details": {}}


class RefereeAgent(Agent):

    def __init__(self):
        super().__init__("referee")
        self.engine = RefereeEngine()

    def analyze(self, match: dict) -> dict:
        result = self.engine.calculate(
            match.get("referee_yellow_avg", 3.0),
            match.get("referee_red_avg", 0.1),
            match.get("referee_penalty_avg", 0.2),
        )
        return {"score": result["discipline"], "prediction": None, "confidence": 45, "details": result}


class OddsAgent(Agent):

    def __init__(self):
        super().__init__("odds")
        self.engine = OddsEngine()

    def analyze(self, match: dict) -> dict:
        odds = match.get("odds", {})
        result = self.engine.market(
            odds.get("home", 2.0), odds.get("draw", 3.3), odds.get("away", 3.5)
        )
        prediction = max(result, key=result.get)
        return {
            "score": result["home"],
            "prediction": prediction.upper() if prediction != "draw" else "DRAW",
            "confidence": 75,
            "details": result,
        }


class StreakAgent(Agent):

    def __init__(self):
        super().__init__("streak")
        self.engine = StreakEngine()

    def analyze(self, match: dict) -> dict:
        result = self.engine.calculate(match.get("recent_streak", []))
        return {"score": result["form"], "prediction": None, "confidence": 50, "details": result}


class PressureAgent(Agent):

    def __init__(self):
        super().__init__("pressure")
        self.engine = PressureEngine()

    def analyze(self, match: dict) -> dict:
        score = self.engine.calculate(
            match.get("derby", False), match.get("final", False), match.get("must_win", False)
        )
        return {"score": score, "prediction": None, "confidence": 40, "details": {}}

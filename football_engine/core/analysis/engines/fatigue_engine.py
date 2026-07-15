"""Yorgunluk analizi"""


class FatigueEngine:

    def calculate(self, travel_km: float, rest_days: int):
        fatigue = travel_km / 100
        fatigue -= rest_days * 5
        fatigue = max(0, fatigue)
        score = max(0, 100 - fatigue)
        return round(score, 2)

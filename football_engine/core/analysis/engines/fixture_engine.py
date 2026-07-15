"""Fikstur yogunlugu analizi"""


class FixtureEngine:

    def calculate(self, matches_last_7_days: int, matches_last_30_days: int):
        score = 100
        score -= matches_last_7_days * 8
        score -= matches_last_30_days * 2
        return max(0, min(100, score))

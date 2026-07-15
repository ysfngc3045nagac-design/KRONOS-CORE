"""Motivasyon analizi"""


class MotivationEngine:

    def calculate(self, league_position: int, title_race: bool, relegation: bool):
        score = 50
        if title_race:
            score += 30
        if relegation:
            score += 20
        if league_position <= 4:
            score += 10
        return min(100, score)

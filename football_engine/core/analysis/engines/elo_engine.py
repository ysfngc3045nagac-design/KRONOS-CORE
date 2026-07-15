"""ELO tabanli guc hesaplama"""


class EloEngine:

    def expected_score(self, home_rating: float, away_rating: float) -> float:
        return 1 / (1 + 10 ** ((away_rating - home_rating) / 400))

    def probability(self, home_rating: float, away_rating: float):
        home = self.expected_score(home_rating, away_rating)
        away = 1 - home
        draw = 0.20
        total = home + away + draw
        return {
            "home": round(home / total * 100, 2),
            "draw": round(draw / total * 100, 2),
            "away": round(away / total * 100, 2),
        }

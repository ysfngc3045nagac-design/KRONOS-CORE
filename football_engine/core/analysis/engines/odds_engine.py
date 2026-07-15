"""Bahis oranlarini olasiliga donusturur (ham, marjsiz)."""


class OddsEngine:

    def implied_probability(self, odd: float) -> float:
        if odd <= 0:
            return 0.0
        return round((1 / odd) * 100, 2)

    def market(self, home, draw, away):
        return {
            "home": self.implied_probability(home),
            "draw": self.implied_probability(draw),
            "away": self.implied_probability(away),
        }

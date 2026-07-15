"""Expected Goals analizi"""


class XGEngine:

    def evaluate(self, xg: float, xga: float):
        attack = min(100, xg * 30)
        defense = max(0, 100 - (xga * 30))
        return {"attack": round(attack, 2), "defense": round(defense, 2)}

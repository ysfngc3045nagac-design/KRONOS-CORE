"""
Gol istatistik motoru

DUZELTME: sadece `scored` bosluguna bakiyordu, `conceded` bos olabilir ve
ZeroDivisionError verirdi. Artik ikisi de kontrol ediliyor.
"""


class GoalEngine:

    def analyze(self, scored: list[int], conceded: list[int]):

        if not scored or not conceded:
            return {"attack": 0, "defense": 0}

        avg_scored = sum(scored) / len(scored)
        avg_conceded = sum(conceded) / len(conceded)

        attack = min(100, avg_scored * 25)
        defense = max(0, 100 - avg_conceded * 25)

        return {"attack": round(attack, 2), "defense": round(defense, 2)}

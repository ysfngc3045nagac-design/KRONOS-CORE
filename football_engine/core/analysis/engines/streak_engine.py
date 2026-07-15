"""
Galibiyet / maglubiyet serileri

DUZELTME: `results` bos liste ise ZeroDivisionError veriyordu. Kontrol eklendi.
"""


class StreakEngine:

    def calculate(self, results: list[str]):

        win = results.count("W")
        draw = results.count("D")
        lose = results.count("L")

        if not results:
            return {"wins": 0, "draws": 0, "losses": 0, "form": 0}

        form = (win * 3 + draw) / (len(results) * 3) * 100

        return {"wins": win, "draws": draw, "losses": lose, "form": round(form, 2)}

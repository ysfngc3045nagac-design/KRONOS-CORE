"""
Hakem analizi

DUZELTME: `discipline` degeri 0'a clamp edilmiyordu, yuksek yellow/red
ortalamalarinda negatif cikabiliyordu. Diger motorlarla tutarlilik icin
max(0, ...) eklendi.
"""


class RefereeEngine:

    def calculate(self, yellow_average: float, red_average: float, penalty_average: float):
        discipline = 100 - yellow_average * 8 - red_average * 20
        return {
            "discipline": round(max(0, discipline), 2),
            "penalty_rate": round(penalty_average * 100, 2),
        }

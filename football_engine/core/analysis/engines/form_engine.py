"""
Son mac form analiz motoru

DUZELTME: orijinalde match.home bayragi hic kullanilmiyordu, puan hep
`home_goals > away_goals` ile hesaplaniyordu - deplasman maclarinda yanlis
sonuc verebiliyordu. Artik takimin kendi perspektifinden (kendi_gol / rakip_gol)
hesaplaniyor.
"""

from dataclasses import dataclass


@dataclass
class MatchResult:
    home_goals: int
    away_goals: int
    home: bool  # takim bu macta ev sahibi miydi?


class FormEngine:

    def calculate(self, matches: list[MatchResult]) -> float:

        if not matches:
            return 50.0

        points = 0

        for match in matches:

            own_goals = match.home_goals if match.home else match.away_goals
            opp_goals = match.away_goals if match.home else match.home_goals

            if own_goals > opp_goals:
                points += 3
            elif own_goals == opp_goals:
                points += 1

        max_points = len(matches) * 3

        return round((points / max_points) * 100, 2)

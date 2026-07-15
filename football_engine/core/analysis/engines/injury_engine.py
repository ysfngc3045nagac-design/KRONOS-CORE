"""Sakat oyuncu etkisi"""


class InjuryEngine:

    def calculate(self, injured_players: int, key_players: int):
        score = 100
        score -= injured_players * 5
        score -= key_players * 10
        return max(0, score)

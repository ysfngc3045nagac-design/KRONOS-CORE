"""Mac baskisi analizi"""


class PressureEngine:

    def calculate(self, derby=False, final=False, must_win=False):
        score = 50
        if derby:
            score += 15
        if final:
            score += 25
        if must_win:
            score += 20
        return min(score, 100)

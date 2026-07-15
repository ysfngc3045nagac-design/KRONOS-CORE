"""Risk puani hesaplar (confidence/consistency/missing_data tabanli)."""


class RiskEngine:

    def calculate(self, confidence, consistency, missing_data):
        risk = 100
        risk -= confidence * 0.5
        risk -= consistency * 0.3
        risk -= max(0, 20 - missing_data)
        return max(0, round(risk, 2))

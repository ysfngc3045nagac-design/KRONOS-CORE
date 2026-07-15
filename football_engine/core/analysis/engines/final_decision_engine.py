"""Skor/guven/riskten sozel karar uretir."""


class FinalDecisionEngine:

    def decide(self, score, confidence, risk):
        if confidence < 60:
            return "Yetersiz Veri"
        if risk > 60:
            return "Yuksek Risk"
        if score >= 80:
            return "Cok Guclu"
        if score >= 70:
            return "Guclu"
        if score >= 60:
            return "Orta"
        return "Zayif"

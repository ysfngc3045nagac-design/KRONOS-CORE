"""Son karar motoru (skor + guven + risk + oylama sonucu birlestirilir)."""


class DecisionEngine:

    def decide(self, score, confidence, risk, voting):

        if confidence < 50:
            return "YETERSIZ VERI"

        if risk > 60:
            return "RISKLI"

        if voting.get("prediction") is None:
            return "KARARSIZ"

        if score >= 60:
            return voting["prediction"]

        return "KARARSIZ"

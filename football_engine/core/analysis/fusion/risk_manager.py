"""Ajanlar arasindaki fikir ayriligina gore risk hesaplar."""


class RiskManager:

    def calculate(self, context):

        predictions = [
            r.get("prediction")
            for r in context.results.values()
            if isinstance(r, dict) and r.get("prediction")
        ]

        if not predictions:
            return 100

        majority = max(set(predictions), key=predictions.count)

        disagreements = sum(1 for p in predictions if p != majority)

        return round(disagreements / len(predictions) * 100, 2)

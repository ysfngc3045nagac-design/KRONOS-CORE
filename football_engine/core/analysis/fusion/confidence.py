"""
Guven katsayisi hesaplayici.

NOT: orijinal versiyon sadece kac ajanin sonuc urettigine bakiyordu
(count * 2), sonuclarin kendi guvenine hic bakmiyordu. Artik her ajanin
kendi confidence degerinin ortalamasi da hesaba katiliyor.
"""


class ConfidenceCalculator:

    def calculate(self, context):

        count = len(context.results)

        if count == 0:
            return 0

        confidences = [
            r.get("confidence", 50)
            for r in context.results.values()
            if isinstance(r, dict)
        ]

        avg_confidence = sum(confidences) / len(confidences) if confidences else 50

        coverage_bonus = min(30, count * 2)

        return round(min(100, avg_confidence * 0.7 + coverage_bonus), 2)

"""
Butun analizlerden tek puan uretir.

NOT: Bu artik calisir durumda - AgentManager'dan gelen tum sonuclar standart
{"score": ...} formatinda oldugu icin (bkz core/analysis/agents/), asagidaki
dongu artik bos liste donmuyor.
"""


class ScoreFusion:

    def calculate(self, context):

        values = []

        for result in context.results.values():
            if isinstance(result, dict):
                score = result.get("score")
                if isinstance(score, (int, float)):
                    values.append(score)

        if not values:
            return 0

        return round(sum(values) / len(values), 2)

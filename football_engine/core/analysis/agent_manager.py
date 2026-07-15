"""
Merkezi Agent yoneticisi.

NOT: Ayni isimde iki AgentManager vardi (biri task-tabanli/registry'siz
constructor, biri registry alan ve hata yakalayan constructor). Bu, hata
yakalayan (try/except) versiyon - bir ajan patlarsa tum analiz durmasin diye
secildi.
"""

from football_engine.core.analysis.context import AnalysisContext


class AgentManager:

    def __init__(self, registry):
        self.registry = registry

    def analyze(self, match: dict) -> AnalysisContext:

        context = AnalysisContext(match)

        for agent in self.registry.all():

            try:
                result = agent.analyze(match)
                context.add_result(agent.name, result)

            except Exception as exc:
                context.add_result(agent.name, {
                    "score": 0,
                    "prediction": None,
                    "confidence": 0,
                    "details": {"error": str(exc)},
                })

        return context

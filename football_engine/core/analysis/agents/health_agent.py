"""
Sistem saglik ajani.

NOT: Bu dosya konusma boyunca defalarca import edildi ama kodu hicbir zaman
paylasilmadi. Diger ajanlardan farkli olarak bir mac tahmini uretmez; sistemin
(model saglayici, veri kaynaklari) analiz yapmaya hazir olup olmadigini
kontrol eder ve bunu standart Agent sozlugu formatinda raporlar - boylece
AgentRegistry/AgentManager icinde diger ajanlarla ayni sekilde calisir ve
sonuc, genel guven skoruna dahil edilebilir.
"""

from football_engine.core.analysis.agent import Agent


class HealthAgent(Agent):

    def __init__(self, monitor=None, model_adapter=None):
        super().__init__("health")
        self.monitor = monitor
        self.model_adapter = model_adapter

    def analyze(self, match: dict) -> dict:

        checks = {}

        if self.monitor is not None:
            checks["system"] = self.monitor.health()

        if self.model_adapter is not None:
            checks["model"] = self.model_adapter.health()

        all_ok = all(bool(v) for v in checks.values()) if checks else True

        return {
            "score": 100 if all_ok else 0,
            "prediction": None,
            "confidence": 100 if checks else 0,
            "details": checks,
        }

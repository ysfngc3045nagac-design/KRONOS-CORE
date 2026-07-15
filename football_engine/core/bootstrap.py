"""
KRONOS Bootstrap

NOT: Sistemde en az ALTI farkli "merkezi giris noktasi" adayi birikmisti:
KronosEngine, AnalysisPipeline, AnalysisManager, MasterAnalysisEngine,
FinalAnalysisEngine (fusion - bu hala kullaniliyor, dogru katmanda),
MasterPipeline, MasterController, Orchestrator, Kernel, KronosApplication
(iki versiyon).

Karar: tek giris noktasi -> KronosApplication (bkz app.py), asagidaki
zincir uzerinden:

    Bootstrap (servisleri kurar)
      -> Orchestrator (AgentManager + FinalAnalysisEngine calistirir)
        -> KronosApplication (disariya tek metodla - analyze() - acilir)

Diger adaylar (KronosEngine, AnalysisPipeline, MasterPipeline, Kernel vb.)
bu pakete DAHIL EDILMEDI - hepsi ayni isi farkli sekilde yapiyordu ve
gercekte kullanilmiyorlardi (dead code). Referans/arsiv olarak istersen
ayrica isteyebilirsin.
"""

from football_engine.core.storage import StorageManager
from football_engine.core.data import DataHub, MockProvider
from football_engine.core.monitoring import SystemMonitor
from football_engine.core.tools.cache import Cache


class Bootstrap:

    def __init__(self):
        self.storage = StorageManager()
        self.datahub = DataHub()
        self.datahub.register(MockProvider(), default=True)
        self.cache = Cache()
        self.monitor = SystemMonitor()

    def initialize(self):
        return {
            "storage": self.storage,
            "datahub": self.datahub,
            "cache": self.cache,
            "monitor": self.monitor,
        }

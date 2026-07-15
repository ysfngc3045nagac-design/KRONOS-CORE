"""
Rapor gecmisi.

NOT: Bu, projede en az UC kez birebir ayni sekilde yazilmisti
(AnalysisHistory, HistoryStore, HistoryManager, ReportHistory). Hepsi ayni
add/latest/all/clear desenini tekrarliyordu. Tek bir kanonik implementasyon
olarak burada tutuluyor; diger katmanlar (analysis, storage, scheduler)
gerektiginde bunu import edip kullanmali, kendi kopyalarini olusturmamali.
"""

from collections import deque


class ReportHistory:

    def __init__(self, limit: int | None = None):
        self.history = deque(maxlen=limit)

    def add(self, report):
        self.history.append(report)

    def latest(self):
        return self.history[-1] if self.history else None

    def all(self):
        return list(self.history)

    def count(self):
        return len(self.history)

    def clear(self):
        self.history.clear()

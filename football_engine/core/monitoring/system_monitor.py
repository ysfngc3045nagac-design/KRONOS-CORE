"""Merkezi sistem izleyici."""

from football_engine.core.monitoring.metrics import Metrics
from football_engine.core.monitoring.performance import PerformanceMonitor
from football_engine.core.monitoring.errors import ErrorRegistry


class SystemMonitor:

    def __init__(self):
        self.metrics = Metrics()
        self.performance = PerformanceMonitor()
        self.errors = ErrorRegistry()

    def health(self):
        return {"metrics": self.metrics.snapshot(), "errors": len(self.errors.all())}

"""Performans olcumu."""

import time


class PerformanceMonitor:

    def __init__(self):
        self._times = {}

    def start(self, key):
        self._times[key] = time.perf_counter()

    def stop(self, key):
        if key not in self._times:
            return 0.0
        elapsed = time.perf_counter() - self._times[key]
        del self._times[key]
        return round(elapsed, 4)

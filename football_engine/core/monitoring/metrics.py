"""KRONOS calisma metrikleri (defaultdict tabanli sayac)."""

from collections import defaultdict


class Metrics:

    def __init__(self):
        self._values = defaultdict(int)

    def increment(self, name, value=1):
        self._values[name] += value

    def set(self, name, value):
        self._values[name] = value

    def get(self, name):
        return self._values.get(name, 0)

    def snapshot(self):
        return dict(self._values)

    def clear(self):
        self._values.clear()

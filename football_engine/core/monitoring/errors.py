"""Hata kayit sistemi."""

from datetime import datetime


class ErrorRegistry:

    def __init__(self):
        self.errors = []

    def add(self, error):
        self.errors.append({"time": datetime.utcnow().isoformat(), "message": str(error)})

    def latest(self):
        return self.errors[-1] if self.errors else None

    def all(self):
        return list(self.errors)

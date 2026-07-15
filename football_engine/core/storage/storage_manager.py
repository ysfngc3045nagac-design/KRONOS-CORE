"""Merkezi depolama yoneticisi - kalici olmayan (in-memory) katman"""

from football_engine.core.storage.memory_repository import MemoryRepository


class StorageManager:

    def __init__(self):
        self.matches = MemoryRepository()
        self.teams = MemoryRepository()
        self.players = MemoryRepository()
        self.reports = MemoryRepository()

    def reset(self):
        self.matches.clear()
        self.teams.clear()
        self.players.clear()
        self.reports.clear()

"""Bellek ici Repository"""

from football_engine.core.storage.repository import Repository


class MemoryRepository(Repository):

    def __init__(self):
        self.data = {}

    def save(self, obj):
        self.data[obj["id"]] = obj

    def get(self, key):
        return self.data.get(key)

    def all(self):
        return list(self.data.values())

    def delete(self, key):
        self.data.pop(key, None)

    def clear(self):
        self.data.clear()

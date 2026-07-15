"""Basit JSON tabanli kalici hafiza"""

import json
from pathlib import Path


class LongTermMemory:

    def __init__(self, filename="memory.json"):
        self.path = Path(filename)
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("{}")

    def load(self):
        return json.loads(self.path.read_text())

    def save(self, data):
        self.path.write_text(json.dumps(data, indent=4, ensure_ascii=False))

    def set(self, key, value):
        data = self.load()
        data[key] = value
        self.save(data)

    def get(self, key, default=None):
        return self.load().get(key, default)

    def delete(self, key):
        data = self.load()
        if key in data:
            del data[key]
            self.save(data)

    def clear(self):
        self.save({})

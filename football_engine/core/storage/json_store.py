"""JSON tabanli kalici (diske yazan) veri saklama."""

import json
from pathlib import Path


class JsonStore:

    def __init__(self, directory="storage"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, filename, data):
        path = self.directory / filename
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def load(self, filename):
        path = self.directory / filename
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

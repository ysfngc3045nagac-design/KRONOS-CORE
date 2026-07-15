"""
Yerel (bellek ici) veri saglayicisi - gercek zamanli veri gelmeden
once test/manuel veri girisi icin kullanilir.
"""

from football_engine.core.data.provider_interface import DataProvider


class LocalProvider(DataProvider):

    def __init__(self):
        self.storage: dict[str, dict] = {}

    def name(self):
        return "local"

    def get_match(self, match_id):
        return self.storage.get(match_id)

    def get_team(self, team_id):
        return {"id": team_id}

    def search_matches(self, date):
        return [m for m in self.storage.values() if m.get("date") == date]

    def add_match(self, match: dict):
        self.storage[match["id"]] = match

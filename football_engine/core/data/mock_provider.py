"""Gelistirme sirasinda kullanilacak ornek veri saglayici."""

from football_engine.core.data.provider_interface import DataProvider


class MockProvider(DataProvider):

    def name(self):
        return "mock"

    def get_match(self, match_id):
        return {"id": match_id, "home": "Team A", "away": "Team B"}

    def get_team(self, team_id):
        return {"id": team_id, "name": "Example Team"}

    def search_matches(self, date):
        return [{"date": date, "home": "Team A", "away": "Team B"}]

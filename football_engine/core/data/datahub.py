"""
Merkezi veri yoneticisi (birlestirilmis: ProviderRegistry + DataHub tek yerde)

NOT: Iki ayri DataHub vardi. Bu versiyon coklu saglayici destekliyor (isimle
secim) + bir "varsayilan" saglayici kavrami. team()/matches() metodlarina da
match() ile ayni RuntimeError korumasi eklendi (orijinalde sadece match()'te
vardi, digerlerinde provider None ise AttributeError verirdi).
"""

from football_engine.core.data.provider_interface import DataProvider


class DataHub:

    def __init__(self):
        self.providers: dict[str, DataProvider] = {}
        self._default_name: str | None = None

    def register(self, provider: DataProvider, default: bool = False):
        self.providers[provider.name()] = provider
        if default or self._default_name is None:
            self._default_name = provider.name()

    def provider_names(self):
        return list(self.providers.keys())

    def get_provider(self, name: str | None = None):
        name = name or self._default_name
        if name is None:
            return None
        return self.providers.get(name)

    def _require_provider(self, name: str | None = None) -> DataProvider:
        provider = self.get_provider(name)
        if provider is None:
            raise RuntimeError("Veri saglayicisi bulunamadi.")
        return provider

    def get_match(self, match_id: str, provider: str | None = None):
        return self._require_provider(provider).get_match(match_id)

    def get_team(self, team_id: str, provider: str | None = None):
        return self._require_provider(provider).get_team(team_id)

    def search(self, date: str, provider: str | None = None):
        return self._require_provider(provider).search_matches(date)

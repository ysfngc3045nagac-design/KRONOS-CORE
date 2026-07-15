"""
Tum veri saglayicilarin uyacagi ortak arayuz.

NOT: iki farkli DataProvider arayuzu vardi:
  1) get_match/get_team/search_matches(date)
  2) get_match/get_team/search_matches()  (parametresiz)
Ilkini (date parametreli) sectim, cunku gercek bir futbol API entegrasyonunda
belirli bir tarihe gore mac aramak zorunlu bir ihtiyac.
"""

from abc import ABC, abstractmethod


class DataProvider(ABC):

    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def get_match(self, match_id: str) -> dict:
        ...

    @abstractmethod
    def get_team(self, team_id: str) -> dict:
        ...

    @abstractmethod
    def search_matches(self, date: str) -> list:
        ...

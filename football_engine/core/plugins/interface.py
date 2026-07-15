"""
Plugin taban sinifi.

NOT: Iki farkli Plugin mimarisi vardi: (name/initialize/shutdown - 3 metod)
ve (name sinif degiskeni + tek setup(app) metodu). 3 metodlu, daha
aciklayici olani sectim (initialize/shutdown ayrimi, plugin'in kaynaklarini
duzgun kapatabilmesi icin onemli).
"""

from abc import ABC, abstractmethod


class Plugin(ABC):

    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def initialize(self, app) -> None:
        ...

    @abstractmethod
    def shutdown(self) -> None:
        ...

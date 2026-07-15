"""
Temel AI Agent sinifi (analiz ajanlari icin ortak arayuz)

NOT: Projede `analyze()` metod adi standart olarak secildi (bazi motorlarda
`calculate()`/`evaluate()`/`decide()` kullanilmisti - Agent katmani bunlari
saracak, motorlarin kendisi degismedi).

Standart cikti sozlugu:
    {
        "score": float (0-100),
        "prediction": "HOME" | "DRAW" | "AWAY" | None,
        "confidence": float (0-100),
        "details": dict,   # motorun ham ciktisi
    }
"""

from abc import ABC, abstractmethod


class Agent(ABC):

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def analyze(self, match: dict) -> dict:
        ...

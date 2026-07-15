"""Genel Repository arayuzu"""

from abc import ABC, abstractmethod


class Repository(ABC):

    @abstractmethod
    def save(self, obj):
        ...

    @abstractmethod
    def get(self, key):
        ...

    @abstractmethod
    def all(self):
        ...

    @abstractmethod
    def delete(self, key):
        ...

"""Ornek eklenti."""

from football_engine.core.plugins.interface import Plugin


class ExamplePlugin(Plugin):

    def name(self):
        return "example"

    def initialize(self, app):
        print("Example Plugin baslatildi")

    def shutdown(self):
        print("Example Plugin durduruldu")

"""Plugin yoneticisi."""

from football_engine.core.plugins.interface import Plugin


class PluginManager:

    def __init__(self):
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin):
        self._plugins[plugin.name()] = plugin

    def initialize(self, app):
        for plugin in self._plugins.values():
            plugin.initialize(app)

    def shutdown(self):
        for plugin in self._plugins.values():
            plugin.shutdown()

    def names(self):
        return list(self._plugins.keys())

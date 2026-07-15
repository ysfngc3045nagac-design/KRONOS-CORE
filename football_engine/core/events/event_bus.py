"""
Merkezi Event Bus (birlestirilmis surum - subscribe/publish)
"""

from collections import defaultdict


class EventBus:

    def __init__(self):
        self._listeners = defaultdict(list)

    def subscribe(self, event_name, callback):
        self._listeners[event_name].append(callback)

    def publish(self, event):
        for callback in self._listeners[event.name]:
            callback(event)

    def unsubscribe_all(self, event_name):
        self._listeners.pop(event_name, None)

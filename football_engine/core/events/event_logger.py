"""
Event Logger - EventBus'a abone olup her olayi loglar
"""

from football_engine.core.logging.logger import KronosLogger


class EventLogger:

    def __init__(self):
        self.logger = KronosLogger()

    def __call__(self, event):
        self.logger.info(f"[EVENT] {event.name} | {event.payload}")

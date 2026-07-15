"""Sistem durum yoneticisi."""

from football_engine.core.state.system_state import SystemState


class StateManager:

    def __init__(self):
        self.state = SystemState.STOPPED

    def set(self, state):
        self.state = state

    def get(self):
        return self.state

    def ready(self):
        self.state = SystemState.READY

    def analyzing(self):
        self.state = SystemState.ANALYZING

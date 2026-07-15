"""Oturum yoneticisi."""

from football_engine.core.session.session import Session


class SessionManager:

    def __init__(self):
        self.sessions: dict[str, Session] = {}

    def get(self, session_id):
        if session_id not in self.sessions:
            self.sessions[session_id] = Session(session_id=session_id)
        return self.sessions[session_id]

    def remove(self, session_id):
        self.sessions.pop(session_id, None)

    def count(self):
        return len(self.sessions)

"""
KRONOS Ana Uygulamasi - tek giris noktasi.

Kullanim:

    from football_engine.core.app import KronosApplication

    app = KronosApplication()
    report = app.analyze({
        "id": "12345",
        "home_elo": 1650, "away_elo": 1500,
        "xg": 1.8, "xga": 0.9,
        "odds": {"home": 1.8, "draw": 3.6, "away": 4.2},
        ...
    })
"""

from football_engine.core.bootstrap import Bootstrap
from football_engine.core.orchestrator import Orchestrator
from football_engine.core.analysis.agent_registry import AgentRegistry
from football_engine.core.analysis.agents import build_default_registry
from football_engine.core.report import ReportManager
from football_engine.core.config.settings import settings


class KronosApplication:

    def __init__(self, agent_registry: AgentRegistry | None = None):

        self.bootstrap = Bootstrap()
        self.services = self.bootstrap.initialize()

        self.registry = agent_registry or build_default_registry()

        self.orchestrator = Orchestrator(self.registry)
        self.reports = ReportManager()

    def analyze(self, match: dict, save: bool = True) -> dict:

        analysis = self.orchestrator.analyze(match)

        if not save:
            return analysis

        match_id = match.get("id", "unknown")
        filename = f"{settings.REPORT_DIRECTORY}/{match_id}.json"

        return self.reports.create(match, analysis, filename)

    def health(self):
        return {
            "monitor": self.services["monitor"].health(),
            "agents": self.registry.count(),
            "reports_saved": self.reports.history.count(),
        }

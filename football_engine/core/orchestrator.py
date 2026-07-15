"""
KRONOS Orchestrator - AgentManager + FinalAnalysisEngine'i birlestirir.
"""

from football_engine.core.analysis.fusion.final_engine import FinalAnalysisEngine
from football_engine.core.analysis.agent_manager import AgentManager


class Orchestrator:

    def __init__(self, agent_registry):
        self.manager = AgentManager(agent_registry)
        self.finalizer = FinalAnalysisEngine()

    def analyze(self, match):
        context = self.manager.analyze(match)
        return self.finalizer.build(context)

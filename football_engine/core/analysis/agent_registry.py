"""Agent kayit sistemi (isim -> Agent nesnesi)"""

from football_engine.core.analysis.agent import Agent


class AgentRegistry:

    def __init__(self):
        self._agents: dict[str, Agent] = {}

    def register(self, agent: Agent):
        self._agents[agent.name] = agent

    def get(self, name):
        return self._agents.get(name)

    def all(self):
        return list(self._agents.values())

    def count(self):
        return len(self._agents)

    def names(self):
        return list(self._agents.keys())

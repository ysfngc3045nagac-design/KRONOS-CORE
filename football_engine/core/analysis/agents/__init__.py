from .form_agent import FormAgent
from .health_agent import HealthAgent
from .engine_agents import (
    GoalAgent, XGAgent, EloAgent, InjuryAgent, HomeAdvantageAgent,
    FixtureAgent, FatigueAgent, WeatherAgent, MotivationAgent,
    RefereeAgent, OddsAgent, StreakAgent, PressureAgent,
)

__all__ = [
    "FormAgent", "HealthAgent", "GoalAgent", "XGAgent", "EloAgent",
    "InjuryAgent", "HomeAdvantageAgent", "FixtureAgent", "FatigueAgent",
    "WeatherAgent", "MotivationAgent", "RefereeAgent", "OddsAgent",
    "StreakAgent", "PressureAgent",
]


def build_default_registry():
    """Tum standart ajanlarla dolu bir AgentRegistry dondurur."""
    from football_engine.core.analysis.agent_registry import AgentRegistry

    registry = AgentRegistry()
    for agent_cls in (
        FormAgent, GoalAgent, XGAgent, EloAgent, InjuryAgent,
        HomeAdvantageAgent, FixtureAgent, FatigueAgent, WeatherAgent,
        MotivationAgent, RefereeAgent, OddsAgent, StreakAgent, PressureAgent,
    ):
        registry.register(agent_cls())

    return registry

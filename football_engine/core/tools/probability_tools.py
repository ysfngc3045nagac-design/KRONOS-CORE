"""Olasilik hesaplama araclari"""

from math import exp
from football_engine.core.tools.registry import tool_registry


def _sigmoid(x: float) -> float:
    return 1 / (1 + exp(-x))


@tool_registry.register(
    name="probability_percent", description="0-1 arasi olasiligi yuzdeye cevirir.",
    parameters={"type": "object", "properties": {"value": {"type": "number"}}, "required": ["value"]},
)
def probability_percent(value: float):
    value = max(0.0, min(1.0, value))
    return round(value * 100, 2)


@tool_registry.register(
    name="weighted_average", description="Agirlikli ortalama hesaplar.",
    parameters={
        "type": "object",
        "properties": {"values": {"type": "array", "items": {"type": "number"}}, "weights": {"type": "array", "items": {"type": "number"}}},
        "required": ["values", "weights"],
    },
)
def weighted_average(values, weights):
    if len(values) != len(weights):
        raise ValueError("Liste uzunluklari esit olmali.")
    total_weight = sum(weights)
    if total_weight == 0:
        return 0
    return sum(v * w for v, w in zip(values, weights)) / total_weight


@tool_registry.register(
    name="normalize_score", description="Skoru 0-100 araligina normalize eder.",
    parameters={
        "type": "object",
        "properties": {"value": {"type": "number"}, "minimum": {"type": "number"}, "maximum": {"type": "number"}},
        "required": ["value", "minimum", "maximum"],
    },
)
def normalize_score(value, minimum, maximum):
    if maximum == minimum:
        return 0
    score = ((value - minimum) / (maximum - minimum)) * 100
    return round(max(0, min(100, score)), 2)


@tool_registry.register(
    name="sigmoid_score", description="Ham skoru olasiliga donusturur.",
    parameters={"type": "object", "properties": {"value": {"type": "number"}}, "required": ["value"]},
)
def sigmoid_score(value):
    return round(_sigmoid(value), 6)

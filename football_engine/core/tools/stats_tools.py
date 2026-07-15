"""Istatistik araclari"""

from statistics import mean, median, mode, pstdev
from football_engine.core.tools.registry import tool_registry


@tool_registry.register(
    name="statistics_mean", description="Sayi listesinin ortalamasini hesaplar.",
    parameters={"type": "object", "properties": {"numbers": {"type": "array", "items": {"type": "number"}}}, "required": ["numbers"]},
)
def statistics_mean(numbers):
    return mean(numbers)


@tool_registry.register(
    name="statistics_median", description="Ortanca degeri hesaplar.",
    parameters={"type": "object", "properties": {"numbers": {"type": "array", "items": {"type": "number"}}}, "required": ["numbers"]},
)
def statistics_median(numbers):
    return median(numbers)


@tool_registry.register(
    name="statistics_mode", description="En sik tekrar eden degeri dondurur.",
    parameters={"type": "object", "properties": {"numbers": {"type": "array", "items": {"type": "number"}}}, "required": ["numbers"]},
)
def statistics_mode(numbers):
    try:
        return mode(numbers)
    except Exception:
        return None


@tool_registry.register(
    name="statistics_std", description="Standart sapmayi hesaplar.",
    parameters={"type": "object", "properties": {"numbers": {"type": "array", "items": {"type": "number"}}}, "required": ["numbers"]},
)
def statistics_std(numbers):
    if len(numbers) < 2:
        return 0
    return pstdev(numbers)

"""Ileri matematik araclari"""

import math
from football_engine.core.tools.registry import tool_registry


@tool_registry.register(
    name="sqrt", description="Bir sayinin karekokunu hesaplar.",
    parameters={"type": "object", "properties": {"value": {"type": "number"}}, "required": ["value"]},
)
def sqrt(value: float):
    return math.sqrt(value)


@tool_registry.register(
    name="power", description="Us alma islemi yapar.",
    parameters={"type": "object", "properties": {"base": {"type": "number"}, "exp": {"type": "number"}}, "required": ["base", "exp"]},
)
def power(base: float, exp: float):
    return math.pow(base, exp)


@tool_registry.register(
    name="factorial", description="Faktoriyel hesaplar.",
    parameters={"type": "object", "properties": {"value": {"type": "integer"}}, "required": ["value"]},
)
def factorial(value: int):
    return math.factorial(value)


@tool_registry.register(
    name="round_number", description="Sayiyi belirtilen basamaga yuvarlar.",
    parameters={"type": "object", "properties": {"value": {"type": "number"}, "digits": {"type": "integer"}}, "required": ["value"]},
)
def round_number(value: float, digits: int = 2):
    return round(value, digits)


@tool_registry.register(
    name="absolute", description="Mutlak deger hesaplar.",
    parameters={"type": "object", "properties": {"value": {"type": "number"}}, "required": ["value"]},
)
def absolute(value: float):
    return abs(value)

"""Liste ve sozluk yardimci araclari"""

from collections import Counter
from football_engine.core.tools.registry import tool_registry


@tool_registry.register(
    name="sort_numbers", description="Sayi listesini kucukten buyuge siralar.",
    parameters={"type": "object", "properties": {"numbers": {"type": "array", "items": {"type": "number"}}}, "required": ["numbers"]},
)
def sort_numbers(numbers: list):
    return sorted(numbers)


@tool_registry.register(
    name="sum_numbers", description="Sayi listesinin toplamini hesaplar.",
    parameters={"type": "object", "properties": {"numbers": {"type": "array", "items": {"type": "number"}}}, "required": ["numbers"]},
)
def sum_numbers(numbers: list):
    return sum(numbers)


@tool_registry.register(
    name="average_numbers", description="Sayi listesinin ortalamasini hesaplar.",
    parameters={"type": "object", "properties": {"numbers": {"type": "array", "items": {"type": "number"}}}, "required": ["numbers"]},
)
def average_numbers(numbers: list):
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)


@tool_registry.register(
    name="max_number", description="Listedeki en buyuk sayiyi dondurur.",
    parameters={"type": "object", "properties": {"numbers": {"type": "array", "items": {"type": "number"}}}, "required": ["numbers"]},
)
def max_number(numbers):
    return max(numbers)


@tool_registry.register(
    name="min_number", description="Listedeki en kucuk sayiyi dondurur.",
    parameters={"type": "object", "properties": {"numbers": {"type": "array", "items": {"type": "number"}}}, "required": ["numbers"]},
)
def min_number(numbers):
    return min(numbers)


@tool_registry.register(
    name="count_values", description="Listedeki tekrar eden degerleri sayar.",
    parameters={"type": "object", "properties": {"values": {"type": "array"}}, "required": ["values"]},
)
def count_values(values):
    return dict(Counter(values))

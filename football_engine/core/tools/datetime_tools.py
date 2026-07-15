"""Tarih / Saat araclari"""

from datetime import datetime, timedelta, timezone
from football_engine.core.tools.registry import tool_registry


@tool_registry.register(
    name="current_datetime", description="Gecerli UTC tarih ve saatini dondurur.",
    parameters={"type": "object", "properties": {}, "required": []},
)
def current_datetime():
    return datetime.now(timezone.utc).isoformat()


@tool_registry.register(
    name="today", description="Bugunun tarihini dondurur.",
    parameters={"type": "object", "properties": {}, "required": []},
)
def today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


@tool_registry.register(
    name="add_days", description="Bir tarihe gun ekler.",
    parameters={
        "type": "object",
        "properties": {"date": {"type": "string"}, "days": {"type": "integer"}},
        "required": ["date", "days"],
    },
)
def add_days(date: str, days: int):
    dt = datetime.strptime(date, "%Y-%m-%d")
    return (dt + timedelta(days=days)).strftime("%Y-%m-%d")


@tool_registry.register(
    name="days_between", description="Iki tarih arasindaki gun farkini hesaplar.",
    parameters={
        "type": "object",
        "properties": {"start": {"type": "string"}, "end": {"type": "string"}},
        "required": ["start", "end"],
    },
)
def days_between(start: str, end: str):
    d1 = datetime.strptime(start, "%Y-%m-%d")
    d2 = datetime.strptime(end, "%Y-%m-%d")
    return (d2 - d1).days

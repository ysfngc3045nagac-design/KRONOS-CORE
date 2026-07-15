"""JSON yardimci araclari"""

import json
from football_engine.core.tools.registry import tool_registry


@tool_registry.register(
    name="json_pretty",
    description="JSON verisini okunabilir hale getirir.",
    parameters={"type": "object", "properties": {"data": {"type": "string"}}, "required": ["data"]},
)
def json_pretty(data: str) -> str:
    try:
        obj = json.loads(data)
        return json.dumps(obj, indent=4, ensure_ascii=False)
    except Exception as exc:
        return f"HATA: {exc}"


@tool_registry.register(
    name="json_validate",
    description="JSON verisinin gecerli olup olmadigini kontrol eder.",
    parameters={"type": "object", "properties": {"data": {"type": "string"}}, "required": ["data"]},
)
def json_validate(data: str) -> str:
    try:
        json.loads(data)
        return "VALID"
    except Exception as exc:
        return f"INVALID: {exc}"


@tool_registry.register(
    name="json_minify",
    description="JSON verisini sikistirir.",
    parameters={"type": "object", "properties": {"data": {"type": "string"}}, "required": ["data"]},
)
def json_minify(data: str) -> str:
    try:
        obj = json.loads(data)
        return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
    except Exception as exc:
        return f"HATA: {exc}"

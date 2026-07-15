"""UUID araclari

DUZELTME: orijinalde `return str(uuid.uuid4()` seklinde kapanmamis parantez
vardi (SyntaxError). Duzeltildi.
"""

import uuid
from football_engine.core.tools.registry import tool_registry


@tool_registry.register(
    name="generate_uuid", description="Yeni UUID uretir.",
    parameters={"type": "object", "properties": {}, "required": []},
)
def generate_uuid() -> str:
    return str(uuid.uuid4())

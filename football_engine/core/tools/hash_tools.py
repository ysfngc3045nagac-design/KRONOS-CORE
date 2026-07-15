"""Hash araclari"""

import hashlib
from football_engine.core.tools.registry import tool_registry


@tool_registry.register(
    name="sha256", description="Metnin SHA256 ozetini uretir.",
    parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
)
def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@tool_registry.register(
    name="md5", description="Metnin MD5 ozetini uretir.",
    parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
)
def md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


@tool_registry.register(
    name="sha1", description="Metnin SHA1 ozetini uretir.",
    parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
)
def sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()

"""Dosya araclari"""

from pathlib import Path
from football_engine.core.tools.registry import tool_registry


@tool_registry.register(
    name="read_text_file", description="UTF-8 metin dosyasini okur.",
    parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
)
def read_text_file(path: str) -> str:
    file = Path(path)
    if not file.exists():
        return "HATA: Dosya bulunamadi."
    if not file.is_file():
        return "HATA: Gecerli dosya degil."
    return file.read_text(encoding="utf-8")


@tool_registry.register(
    name="write_text_file", description="UTF-8 metin dosyasi olusturur.",
    parameters={
        "type": "object",
        "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
        "required": ["path", "content"],
    },
)
def write_text_file(path: str, content: str) -> str:
    file = Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content, encoding="utf-8")
    return "OK"


@tool_registry.register(
    name="list_directory", description="Bir klasordeki dosyalari listeler.",
    parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
)
def list_directory(path: str):
    folder = Path(path)
    if not folder.exists():
        return []
    return sorted([item.name for item in folder.iterdir()])


@tool_registry.register(
    name="file_exists", description="Dosyanin varligini kontrol eder.",
    parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
)
def file_exists(path: str) -> bool:
    return Path(path).exists()

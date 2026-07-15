"""
Merkezi Tool Registry

Not: iki farkli registry stili vardi (Dict[str, Callable] basit sozluk,
ve decorator tabanli name/description/parameters kayit sistemi). Decorator
tabanli olani sectim cunku tools/*.py dosyalarinin cogu ona gore yazilmis
ve bir LLM tool-calling dongusune (dispatcher) baglanmaya daha uygun.
"""

from typing import Callable, Dict, Any


class ToolRegistry:

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, description: str = "", parameters: dict | None = None):

        def decorator(func: Callable):
            self._tools[name] = {
                "func": func,
                "description": description,
                "parameters": parameters or {"type": "object", "properties": {}, "required": []},
            }
            return func

        return decorator

    def unregister(self, name: str):
        self._tools.pop(name, None)

    def exists(self, name: str) -> bool:
        return name in self._tools

    def get(self, name: str):
        entry = self._tools.get(name)
        return entry["func"] if entry else None

    def list_tools(self):
        return sorted(self._tools.keys())

    def specs(self):
        """LLM tool-calling icin (Anthropic/Gemini uyumlu) tanim listesi."""
        return [
            {
                "name": name,
                "description": entry["description"],
                "parameters": entry["parameters"],
            }
            for name, entry in self._tools.items()
        ]

    def execute(self, name: str, **kwargs):
        entry = self._tools.get(name)

        if entry is None:
            raise ValueError(f"Arac bulunamadi: {name}")

        return entry["func"](**kwargs)


tool_registry = ToolRegistry()

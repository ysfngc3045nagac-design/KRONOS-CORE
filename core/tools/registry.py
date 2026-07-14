"""
core/tools/registry.py

Kronos'un elindeki "araçların" (fonksiyonların) merkezi kayıt defteri.
Yeni bir yetenek eklemek istediğinde (örn. "hava durumu sorgula",
"veritabanına yaz") sadece @tool_registry.register ile işaretlenmiş
bir fonksiyon yazman yeterli — dispatcher otomatik olarak görür.
"""

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class RegisteredTool:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema formatında parametre tanımı
    handler: Callable[..., Any]


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, RegisteredTool] = {}

    def register(self, name: str, description: str, parameters: dict[str, Any]):
        """
        Dekoratör olarak kullanılır:

            @tool_registry.register(
                name="get_weather",
                description="Belirli bir şehrin güncel hava durumunu getirir",
                parameters={
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            )
            def get_weather(city: str) -> dict:
                ...
        """
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._tools[name] = RegisteredTool(
                name=name, description=description, parameters=parameters, handler=func
            )
            return func

        return decorator

    def get(self, name: str) -> RegisteredTool:
        if name not in self._tools:
            raise KeyError(f"Kayıtlı araç bulunamadı: {name}")
        return self._tools[name]

    def execute(self, name: str, arguments: dict[str, Any]) -> Any:
        tool = self.get(name)
        return tool.handler(**arguments)

    def as_anthropic_tools(self) -> list[dict[str, Any]]:
        """Anthropic API'nin beklediği 'tools' formatına dönüştürür."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.parameters,
            }
            for t in self._tools.values()
        ]

    def list_names(self) -> list[str]:
        return list(self._tools.keys())


# Tüm uygulama boyunca tek bir kayıt defteri kullanılır (singleton)
tool_registry = ToolRegistry()

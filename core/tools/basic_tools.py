"""
core/tools/basic_tools.py

Kronos'un ilk gerçek araçları. Yeni bir araç eklemek istediğinde
buraya (ya da yeni bir dosyaya) aynı @tool_registry.register deseniyle
bir fonksiyon daha eklemen yeterli.
"""

from datetime import datetime, timezone

from core.tools.registry import tool_registry


@tool_registry.register(
    name="calculator",
    description="Basit bir matematik ifadesini hesaplar (örn. '12 * (3 + 4)').",
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Hesaplanacak matematik ifadesi, örn. '2 + 2 * 5'",
            }
        },
        "required": ["expression"],
    },
)
def calculator(expression: str) -> str:
    # Güvenlik için sadece sayılar ve temel operatörlere izin veriyoruz.
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        return "HATA: İfade sadece sayılar ve + - * / ( ) içerebilir."
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as exc:
        return f"HATA: İfade hesaplanamadı ({exc})"


@tool_registry.register(
    name="get_current_time",
    description="Şu anki güncel tarih ve saati (UTC) döndürür.",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
def get_current_time() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

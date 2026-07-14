"""
interface/api/main.py

Kronos'un dış dünyaya açılan kapısı. Faz 1'de tek endpoint var: /chat.
Render'a deploy edildiğinde bu dosya çalışan servistir.

Çalıştırmak için (yerelde): uvicorn interface.api.main:app --reload
"""

from fastapi import FastAPI
from pydantic import BaseModel

from core.models.anthropic_adapter import AnthropicAdapter
from core.tools.registry import tool_registry
from orchestration.dispatcher import Dispatcher

app = FastAPI(title="Kronos", version="0.1.0")

_model = AnthropicAdapter()
_dispatcher = Dispatcher(
    model=_model,
    tools=tool_registry,
    system_prompt="Sen Kronos'sun: yardımsever, doğrudan konuşan bir asistansın.",
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model": _model.name(), "tools": tool_registry.list_names()}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    reply = _dispatcher.handle_message(request.message)
    return ChatResponse(reply=reply)

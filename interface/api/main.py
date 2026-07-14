"""
interface/api/main.py

Kronos'un dış dünyaya açılan kapısı.

Faz 2 eklentileri:
  - /: basit bir web sohbet arayüzü (tarayıcıdan doğrudan konuşulabilir)
  - /chat: artık session_id kabul ediyor, konuşmalar SQLite'ta kalıcı
  - Araçlar: core/tools/basic_tools.py içindeki calculator ve
    get_current_time otomatik olarak yükleniyor

Hangi model sağlayıcısının kullanılacağı MODEL_PROVIDER ortam değişkeni
ile seçilir: "anthropic" veya "gemini" (varsayılan: gemini).

Çalıştırmak için (yerelde): uvicorn interface.api.main:app --reload
"""

import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Araçların @tool_registry.register dekoratörleri burada devreye girsin diye
# modülü import ediyoruz (yan etkisi: araçlar registry'ye kaydolur).
from core.tools import basic_tools  # noqa: F401
from core.tools.registry import tool_registry
from core.memory.persistent import PersistentMemory
from orchestration.dispatcher import Dispatcher

app = FastAPI(title="Kronos", version="0.2.0")


def _build_model():
    provider = os.environ.get("MODEL_PROVIDER", "groq").lower()

    if provider == "anthropic":
        from core.models.anthropic_adapter import AnthropicAdapter
        return AnthropicAdapter()

    if provider == "gemini":
        from core.models.gemini_adapter import GeminiAdapter
        return GeminiAdapter()

    if provider == "groq":
        from core.models.groq_adapter import GroqAdapter
        return GroqAdapter()

    raise RuntimeError(
        f"Bilinmeyen MODEL_PROVIDER: '{provider}'. 'anthropic', 'gemini' veya 'groq' olmalı."
    )


_model = _build_model()
_SYSTEM_PROMPT = "Sen Kronos'sun: yardımsever, doğrudan konuşan bir asistansın."

# Her session_id için ayrı bir Dispatcher (ayrı kalıcı hafıza) tutuyoruz.
_dispatchers: dict[str, Dispatcher] = {}


def _get_dispatcher(session_id: str) -> Dispatcher:
    if session_id not in _dispatchers:
        _dispatchers[session_id] = Dispatcher(
            model=_model,
            tools=tool_registry,
            system_prompt=_SYSTEM_PROMPT,
            memory=PersistentMemory(session_id=session_id),
        )
    return _dispatchers[session_id]


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model": _model.name(), "tools": tool_registry.list_names()}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    dispatcher = _get_dispatcher(request.session_id)
    reply = dispatcher.handle_message(request.message)
    return ChatResponse(reply=reply)


@app.get("/", response_class=HTMLResponse)
def chat_ui() -> str:
    return _CHAT_HTML


_CHAT_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kronos</title>
<style>
  body { font-family: -apple-system, sans-serif; max-width: 640px; margin: 0 auto;
         padding: 16px; background: #0f1115; color: #e6e6e6; }
  h1 { font-size: 1.3rem; }
  #log { border: 1px solid #333; border-radius: 8px; padding: 12px; height: 60vh;
         overflow-y: auto; margin-bottom: 12px; background: #1a1d24; }
  .msg { margin-bottom: 10px; line-height: 1.4; white-space: pre-wrap; }
  .user { color: #8ab4f8; }
  .bot { color: #e6e6e6; }
  form { display: flex; gap: 8px; }
  input { flex: 1; padding: 10px; border-radius: 6px; border: 1px solid #333;
          background: #1a1d24; color: #fff; }
  button { padding: 10px 16px; border-radius: 6px; border: none;
           background: #8ab4f8; color: #0f1115; font-weight: bold; }
</style>
</head>
<body>
<h1>🕐 Kronos</h1>
<div id="log"></div>
<form id="f">
  <input id="msg" autocomplete="off" placeholder="Bir şey sor..." />
  <button type="submit">Gönder</button>
</form>
<script>
const log = document.getElementById('log');
const form = document.getElementById('f');
const input = document.getElementById('msg');
const sessionId = localStorage.getItem('kronos_session') ||
  (() => { const id = 'web-' + Math.random().toString(36).slice(2);
            localStorage.setItem('kronos_session', id); return id; })();

function addMsg(text, cls) {
  const div = document.createElement('div');
  div.className = 'msg ' + cls;
  div.textContent = (cls === 'user' ? '🧑 ' : '🕐 ') + text;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  addMsg(text, 'user');
  input.value = '';
  addMsg('...', 'bot');
  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: text, session_id: sessionId})
    });
    const data = await res.json();
    log.lastChild.textContent = '🕐 ' + (data.reply || 'Hata oluştu.');
  } catch (err) {
    log.lastChild.textContent = '🕐 Bağlantı hatası.';
  }
});
</script>
</body>
</html>
"""

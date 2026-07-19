"""
interface/api/main.py

Kronos'un dış dünyaya açılan kapısı.

Faz 3 eklentileri:
  - Mistral sağlayıcı seçeneği eklendi
  - Fütbol puan durumu aracı (get_football_standings)
  - Fütbol maç analizi aracı (analyze_football_match, 14 motor)
  - Saatlik arka plan zamanlayıcısı: Süper Lig, Premier Lig ve Şampiyonlar
    Ligi puan durumlarını önbelleğe alır (servis ayaktayken)

Hangi model sağlayıcısının kullanılacağı MODEL_PROVIDER ortam değişkeni
ile seçilir: "anthropic", "gemini", "groq" veya "mistral" (varsayılan: groq).

Çalıştırmak için (yerelde): uvicorn interface.api.main:app --reload
"""

import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Araçların @tool_registry.register dekoratörleri burada devreye girsin diye
# modülleri import ediyoruz (yan etkisi: araçlar registry'ye kaydolur).
from core.tools import basic_tools  # noqa: F401
from core.tools import football_tools  # noqa: F401
from core.tools import data_hub_tools  # noqa: F401
from core.tools import football_analysis_tools  # noqa: F401
from core.tools.registry import tool_registry
from core.memory.persistent import PersistentMemory
from core.memory import football_store
from orchestration.dispatcher import Dispatcher
from orchestration.scheduler import Scheduler

app = FastAPI(title="Kronos", version="0.3.0")


def _build_model():
    provider = os.environ.get("MODEL_PROVIDER", "brain").lower()

    if provider == "anthropic":
        from core.models.anthropic_adapter import AnthropicAdapter
        return AnthropicAdapter()

    if provider == "gemini":
        from core.models.gemini_adapter import GeminiAdapter
        return GeminiAdapter()

    if provider == "groq":
        from core.models.groq_adapter import GroqAdapter
        return GroqAdapter()

    if provider == "mistral":
        from core.models.mistral_adapter import MistralAdapter
        return MistralAdapter()

    if provider == "cerebras":
        from core.models.cerebras_adapter import CerebrasAdapter
        return CerebrasAdapter()

    if provider == "deepseek":
        from core.models.deepseek_adapter import DeepseekAdapter
        return DeepseekAdapter()

    if provider == "openrouter":
        from core.models.openrouter_adapter import OpenRouterAdapter
        return OpenRouterAdapter()

    if provider == "brain":
        return _build_brain()

    raise RuntimeError(
        f"Bilinmeyen MODEL_PROVIDER: '{provider}'. "
        "'brain', 'anthropic', 'gemini', 'groq', 'mistral', 'cerebras', "
        "'deepseek' veya 'openrouter' olmalı."
    )


def _build_brain():
    """
    Otomatik yedekleme zinciri: Groq → Mistral → Gemini → Cerebras → DeepSeek.
    Sadece ortam değişkeni (API anahtarı) tanımlı olan sağlayıcılar zincire
    dahil edilir - anahtarı olmayan sağlayıcı sessizce atlanır.
    """
    from core.models.brain_adapter import BrainAdapter

    candidates = [
        ("GROQ_API_KEY", "core.models.groq_adapter", "GroqAdapter"),
        ("MISTRAL_API_KEY", "core.models.mistral_adapter", "MistralAdapter"),
        ("CEREBRAS_API_KEY", "core.models.cerebras_adapter", "CerebrasAdapter"),
        ("DEEPSEEK_API_KEY", "core.models.deepseek_adapter", "DeepseekAdapter"),
        ("GEMINI_API_KEY", "core.models.gemini_adapter", "GeminiAdapter"),
    ]

    adapters = []
    for env_key, module_path, class_name in candidates:
        if not os.environ.get(env_key):
            continue
        module = __import__(module_path, fromlist=[class_name])
        adapter_cls = getattr(module, class_name)
        try:
            adapters.append(adapter_cls())
        except Exception as exc:
            print(f"[Kronos] {class_name} başlatılamadı: {exc}")

    return BrainAdapter(adapters)


_model = _build_model()
_SYSTEM_PROMPT = """Sen Kronos'sun: futbol maç analizi konusunda uzmanlaşmış,
doğrudan konuşan bir asistansın.

KRİTİK KURALLAR (futbol maçı, takım veya bahis analizi soruları için):

1. Bir kullanıcı bir maçı analiz etmeni istediğinde, İLK ÖNCE
   `fetch_real_match_data` aracını çağır (home_team, away_team ile).
   Bu araç Kronos'un kendi veritabanından GERÇEK veri getirir (elo, form,
   sakatlık, oranlar). Bu adımı asla atlama, asla kendi bildiğin/tahmin
   ettiğin istatistiklerle direkt `analyze_football_match`'i çağırma.

2. `fetch_real_match_data` sonucunda `home_team_found` veya
   `away_team_found` false ise, ya da `error` alanı varsa: bu takım(lar)
   hakkında ASLA istatistik, form, sakatlık, oran UYDURMA. Kullanıcıya
   açıkça "bu takım için veritabanımda veri yok" de. Var olmayan bir takımı
   (ör. yanlış ülke/lig, yanlış isim) varmış gibi ele alma.

3. `fetch_real_match_data` bir alanı döndürmüyorsa (örn. odds yok), o alanı
   `analyze_football_match`'e de gönderme - motor eksik alanları zaten nötr
   varsayılana düşürür. Eksik veriyi kendi tahminlerinle doldurma.

4. Sadece gerçekten dönen `match_data` içeriğini `analyze_football_match`
   aracına ilet. Analiz sonucunu yorumlarken de motorun ürettiği
   sayılardan/kararlardan sapma; kendi ek tahminini ekleme.

5. Kullanıcı puan durumu isterse `get_football_standings` aracını kullan.

6. Emin olmadığın hiçbir sayısal veriyi (skor, oran, istatistik) asla
   kendi kafandan üretme - ya bir araçtan gelen gerçek veriyi kullan ya da
   verinin eksik olduğunu söyle."""

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


def _refresh_football_cache() -> None:
    for league_key in football_tools.LEAGUES:
        try:
            table = football_tools.fetch_league_table(league_key)
            football_store.save_standings(
                league_key, football_tools.LEAGUES[league_key]["name"], table
            )
        except Exception as exc:
            print(f"[Kronos] {league_key} verisi çekilemedi: {exc}")


_scheduler = Scheduler()
_scheduler.add_interval_job("football_standings_refresh", 3600, _refresh_football_cache)


@app.on_event("startup")
def _on_startup() -> None:
    _scheduler.start()


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

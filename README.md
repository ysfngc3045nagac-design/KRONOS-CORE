# Kronos — Faz 1

Kronos'un ilk, minimal çalışan çekirdeği. Amaç: büyük mimariyi baştan
inşa etmek değil, en küçük çalışan "beyni" ayağa kaldırıp gerçekten
işe yarıyorsa üstüne büyümek.

## Şu an ne var

```
kronos/
├── core/
│   ├── models/
│   │   ├── interface.py          # Model-agnostik sözleşme
│   │   └── anthropic_adapter.py  # Claude implementasyonu
│   ├── tools/
│   │   └── registry.py           # Araç kayıt defteri
│   └── memory/
│       └── short_term.py         # Konuşma geçmişi
├── orchestration/
│   └── dispatcher.py             # Model + hafıza + araçları birbirine bağlar
├── interface/
│   └── api/
│       └── main.py               # FastAPI servisi (/chat, /health)
└── requirements.txt
```

Henüz **yok** (ihtiyaç doğunca eklenecek): `teams/` (uzman ekipler),
`core/memory/medium_term.py` ve `long_term.py`, `core/security/`,
`infrastructure/` (Docker/k8s). Bunları şimdiden yazmak, henüz
kullanılmayan koda bakım yükü eklemek olurdu.

## Kurulum (Render)

1. Bu dosyaları yeni bir GitHub reposuna yükle (KRONOS-AI'dan **ayrı** repo).
2. Render'da yeni bir Web Service oluştur, bu reposu bağla.
3. Start command: `uvicorn interface.api.main:app --host 0.0.0.0 --port $PORT`
4. Environment variable ekle: `ANTHROPIC_API_KEY`

## Test

```
GET /health   → { "status": "ok", "model": "...", "tools": [...] }
POST /chat    → { "message": "merhaba" }  ⇒  { "reply": "..." }
```

## Nasıl büyütülür

- **Yeni araç eklemek:** `core/tools/registry.py`'deki `tool_registry.register`
  dekoratörüyle yeni bir fonksiyon yaz, `interface/api/main.py`'de import et.
- **Yeni model eklemek:** `ModelAdapter`'ı miras alan yeni bir adaptör dosyası
  yaz (örn. `openai_adapter.py`), dispatcher'a hiç dokunmana gerek yok.
- **Uzman ekipler (teams/):** Tek bir dispatcher yetmemeye başlayınca (örn.
  "futbol analiz ekibi" + "genel asistan ekibi" ayrı ayrı gerekiyorsa) bu
  aşamada eklenecek.

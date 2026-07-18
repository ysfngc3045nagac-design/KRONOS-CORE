# KRONOS_DATA_HUB v1.0.0 (duzeltilmis)

Akilli futbol veri toplama sistemi.

## Bu surumde yapilan duzeltme
`main.py` paketleri **mutlak** import ile cagiriyor (`from database import ...`, `from core import ...`),
ama `core/source_manager.py`, `collectors/base_collector.py` ve `core/source_discovery.py`
orijinal halinde **iki noktali relative import** kullaniyordu (`from ..database...`).
Bu, sistemi calistirinca `ImportError: attempted relative import beyond top-level package`
hatasiyla cokertiyordu. Bu 3 dosyadaki importlar main.py ile tutarli hale getirildi ve
sistem gercekten baslatilip test edildi (`initialize_system()` + `--mode dashboard` calisti).

## Onemli not
Agac diyagraminda gecen bazi dosyalar (fotmob.py, flashscore.py, openfootball.py,
injuries.py, transfers.py, github_sources.py, dashboard/web_app.py, scripts/,
Dockerfile, docker-compose.yml, Makefile, .env.example) icin hic kod paylasilmadi,
bu yuzden bu pakette yoklar. `config/sources.json` da sadece kodu yazilan 8 kaynagi iceriyor.

## Calistirma
```bash
pip install -r requirements.txt
python3 main.py --mode dashboard
python3 main.py --mode collect --source football_data --league E0 --season 2425
python3 main.py --mode validate
```

## Kronos (football_engine) ile entegrasyon
Bu proje kendi SQLite semasini (matches/teams/odds/...) kullanir. Kronos'un
`analyze()` fonksiyonunun bekledigi `home_elo, away_elo, xg, xga, scored[], conceded[], odds{}`
seklindeki match sozlugu icin ayri bir adaptor katmani (`data_hub_provider.py`) gerekir;
bu pakette henuz yok.

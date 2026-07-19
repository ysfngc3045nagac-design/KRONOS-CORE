"""
core/tools/data_hub_tools.py

Kronos chat botunun `kronos_data_hub` servisine (ayrı bir Render servisi)
HTTP üzerinden bağlanmasını sağlayan araç. Bu dosya olmadan önce chat botu
ile veri toplama sistemi arasında HİÇBİR bağlantı yoktu - model maç
istatistiklerini (elo, form, oranlar, sakatlık) kendi kafasından uyduruyordu.

Ortam değişkeni gerekli: DATA_HUB_URL
  Örnek: https://kronos-data-hub-xxxx.onrender.com
  (Render'da: kronos-data-hub servisinin public URL'i)

Eğer DATA_HUB_URL tanımlı değilse, araç net bir hata döner - model bu
durumda veriyi UYDURMAMALI, kullanıcıya veri kaynağına ulaşılamadığını
söylemeli (bkz. sistem promptu).
"""

import os

import requests

from core.tools.registry import tool_registry

DATA_HUB_URL = os.environ.get("DATA_HUB_URL", "").rstrip("/")


@tool_registry.register(
    name="fetch_real_match_data",
    description=(
        "Kronos Data Hub'dan bir maç için GERÇEK, veritabanından gelen veriyi "
        "çeker: elo puanları, son 5 maçlık form, gol/yenilen gol listesi, "
        "sakat oyuncu sayısı, güncel bahis oranları. "
        "ÖNEMLİ: analyze_football_match aracını çağırmadan ÖNCE, mümkün "
        "olduğunca bu aracı çağır ve dönen 'match_data' alanını olduğu gibi "
        "analyze_football_match'e ilet. Bu araç bir alanı döndürmüyorsa "
        "(örn. odds yoksa), o alanı UYDURMA - eksik bırak veya kullanıcıya "
        "söyle. 'home_team_found'/'away_team_found' false ise takım "
        "veritabanında yok demektir, o takım hakkında istatistik uydurma."
    ),
    parameters={
        "type": "object",
        "properties": {
            "home_team": {"type": "string", "description": "Ev sahibi takım adı"},
            "away_team": {"type": "string", "description": "Deplasman takımı adı"},
        },
        "required": ["home_team", "away_team"],
    },
)
def fetch_real_match_data(home_team: str, away_team: str) -> dict:
    if not DATA_HUB_URL:
        return {
            "error": (
                "DATA_HUB_URL ortam değişkeni tanımlı değil, veri hub'ına "
                "bağlanılamıyor. Kullanıcıya gerçek veri kaynağına şu an "
                "ulaşılamadığını söyle, istatistik UYDURMA."
            )
        }

    try:
        resp = requests.get(
            f"{DATA_HUB_URL}/match_data",
            params={"home": home_team, "away": away_team},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        return {
            "error": (
                f"Data hub'a ulaşılamadı ({exc}). Kullanıcıya gerçek veri "
                "çekilemediğini söyle, istatistik UYDURMA."
            )
        }

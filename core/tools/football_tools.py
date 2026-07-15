"""
core/tools/football_tools.py

Kronos'un fütbol araçları. Veri kaynağı: TheSportsDB'nin ücretsiz,
kayıt gerektirmeyen API'si (anahtar: "3").

Takip edilen ligler: Süper Lig, Premier Lig, UEFA Şampiyonlar Ligi.
Bu sözlüğe yeni bir lig eklemek için sadece bir satır eklemen yeterli.
"""

from datetime import datetime

import requests

from core.memory import football_store
from core.tools.registry import tool_registry

THESPORTSDB_BASE = "https://www.thesportsdb.com/api/v1/json/3"

LEAGUES = {
    "super_lig": {"id": 4339, "name": "Süper Lig"},
    "premier_lig": {"id": 4328, "name": "Premier Lig"},
    "sampiyonlar_ligi": {"id": 4480, "name": "UEFA Şampiyonlar Ligi"},
}


def _current_season() -> str:
    now = datetime.utcnow()
    if now.month >= 7:
        return f"{now.year}-{now.year + 1}"
    return f"{now.year - 1}-{now.year}"


def fetch_league_table(league_key: str) -> list[dict]:
    """TheSportsDB'den canlı puan durumunu çeker (network gerektirir)."""
    league = LEAGUES[league_key]
    season = _current_season()
    url = f"{THESPORTSDB_BASE}/lookuptable.php"
    resp = requests.get(url, params={"l": league["id"], "s": season}, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data.get("table") or []


def _format_table(league_name: str, table: list[dict], updated_at: str = "") -> str:
    if not table:
        return f"{league_name} için puan durumu şu anda alınamadı (sezon henüz başlamamış olabilir)."

    lines = [f"{league_name} Puan Durumu" + (f" (güncelleme: {updated_at})" if updated_at else "")]
    lines.append("Sıra | Takım | O | G | B | M | Puan")
    for row in table[:10]:
        lines.append(
            f"{row.get('intRank')}. {row.get('strTeam')} | "
            f"{row.get('intPlayed')} | {row.get('intWin')} | "
            f"{row.get('intDraw')} | {row.get('intLoss')} | {row.get('intPoints')}"
        )
    return "\n".join(lines)


@tool_registry.register(
    name="get_football_standings",
    description=(
        "Süper Lig, Premier Lig veya UEFA Şampiyonlar Ligi'nin güncel puan durumunu döndürür."
    ),
    parameters={
        "type": "object",
        "properties": {
            "league": {
                "type": "string",
                "enum": ["super_lig", "premier_lig", "sampiyonlar_ligi"],
                "description": "Hangi ligin puan durumu istendiği",
            }
        },
        "required": ["league"],
    },
)
def get_football_standings(league: str) -> str:
    if league not in LEAGUES:
        return f"HATA: Bilinmeyen lig '{league}'. Geçerli değerler: {list(LEAGUES.keys())}"

    league_name = LEAGUES[league]["name"]

    # Önce zamanlayıcının önbelleğe aldığı veriye bak (hızlı, network gerekmez).
    cached = football_store.load_standings(league)
    if cached:
        return _format_table(cached["league_name"], cached["table"], cached["updated_at"])

    # Önbellek boşsa (zamanlayıcı henüz çalışmadıysa) canlı çek.
    try:
        table = fetch_league_table(league)
    except Exception as exc:
        return f"HATA: {league_name} verisi alınamadı ({exc})"

    return _format_table(league_name, table)

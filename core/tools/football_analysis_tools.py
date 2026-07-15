"""
core/tools/football_analysis_tools.py

Kronos'un fütbol maç analizi aracı. Gerçek motor `football_engine/`
altında izole bir pakette yaşıyor (Yusuf'un hazırlattığı 4 paketlik,
14 ajanlı, test edilmiş analiz sistemi - core/app.py:KronosApplication).

Bu dosya sadece ince bir köprü: Kronos'un konuşma sırasında topladığı
maç bilgilerini KronosApplication.analyze()'e iletir ve sonucu okunabilir
Türkçe metne çevirir.
"""

import os

from football_engine.core.app import KronosApplication
from core.tools.registry import tool_registry

# Render'ın ücretsiz planında ana dizin salt-okunur olabileceği için
# raporları /tmp altına yazıyoruz (Render'da /tmp yazılabilir).
os.environ.setdefault("REPORT_DIRECTORY", "/tmp/kronos_reports")

_app = KronosApplication()


def _format_report(home_team: str, away_team: str, report: dict) -> str:
    analysis = report["analysis"]
    lines = [f"⚽ {home_team} vs {away_team} — Analiz Sonucu", ""]
    lines.append(f"Genel Skor: {analysis['overall_score']}")
    lines.append(f"Güven: {analysis['confidence']}")
    lines.append(f"Risk: {analysis['risk']}")
    lines.append(f"Tahmin: {analysis['prediction'] or 'Belirsiz'}")
    lines.append(f"Karar: {analysis['decision']}")
    lines.append(f"Oylar: {analysis['votes']}")
    lines.append("")
    lines.append("Ajan bazlı detaylar:")
    for agent_name, detail in analysis["details"].items():
        lines.append(
            f"  - {agent_name}: skor={detail.get('score')}, "
            f"tahmin={detail.get('prediction')}, güven={detail.get('confidence')}"
        )
    return "\n".join(lines)


@tool_registry.register(
    name="analyze_football_match",
    description=(
        "Bir futbol maçını 14 farklı motor (form, gol, xG, elo, sakatlık, ev "
        "sahibi avantajı, fikstür yoğunluğu, yorgunluk, hava durumu, motivasyon, "
        "hakem, oranlar, seri, baskı) ile analiz eder ve bir tahmin/karar üretir. "
        "Bilinmeyen veriler otomatik olarak nötr varsayılan değerlere düşer, o "
        "yüzden sadece bildiğin alanları doldurman yeterli."
    ),
    parameters={
        "type": "object",
        "properties": {
            "home_team": {"type": "string", "description": "Ev sahibi takım adı"},
            "away_team": {"type": "string", "description": "Deplasman takımı adı"},
            "match_data": {
                "type": "object",
                "description": (
                    "Bilinen maç verileri. Örnek alanlar: recent_results "
                    "(liste: [{home_goals, away_goals, home}]), scored/conceded "
                    "(gol listeleri), xg/xga (sayı), home_elo/away_elo (sayı), "
                    "injured_players/key_players_injured (sayı), "
                    "home_win_rate/attendance_rate, "
                    "matches_last_7_days/matches_last_30_days, "
                    "travel_km/rest_days, temperature/wind_speed/rain, "
                    "league_position/title_race/relegation, "
                    "referee_yellow_avg/referee_red_avg/referee_penalty_avg, "
                    "odds ({home, draw, away}), recent_streak (liste), "
                    "derby/final/must_win (bool)."
                ),
            },
        },
        "required": ["home_team", "away_team"],
    },
)
def analyze_football_match(home_team: str, away_team: str, match_data: dict | None = None) -> str:
    match = dict(match_data or {})
    match.setdefault("home", True)
    match.setdefault("id", f"{home_team}-{away_team}")

    try:
        report = _app.analyze(match)
    except Exception as exc:
        return f"HATA: Analiz sırasında bir sorun oluştu ({exc})"

    return _format_report(home_team, away_team, report)

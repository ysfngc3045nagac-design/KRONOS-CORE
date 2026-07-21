"""
KRONOS_DATA_HUB - Web Server
Bu dosya, veri toplama sistemini bir web sayfasi/API olarak disariya acar.
Render'da ayri bir Web Service olarak calistirilmak icin tasarlandi.

DUZELTME (bu surum): /match_data endpoint'i eklendi. Bu endpoint olmadan
chat botunun fetch_real_match_data araci her cagrida 404 aliyordu ve
gercek veriye hicbir zaman ulasamiyordu.
"""
import os
import subprocess
from datetime import datetime
from flask import Flask, jsonify, render_template_string, redirect, request
from database.sqlite_manager import SQLiteManager
from core.source_manager import SourceManager
from drive_sync import download_db_from_drive, upload_db_to_drive

app = Flask(__name__)

DB_PATH = os.environ.get("KRONOS_DB_PATH", "data/kronos.db")

# DUZELTME (Drive kalicilik): uygulama baslamadan once Drive'daki guncel
# veritabanini indirmeyi dene. Render diski her deploy/restart'ta sifirlandigi
# icin bu adim olmadan toplanan tum veri kaybolurdu.
download_db_from_drive(DB_PATH)

db = SQLiteManager(db_path=DB_PATH)
source_manager = SourceManager(db=db)

TABLES = [
    "leagues", "teams", "players", "matches", "match_statistics",
    "odds", "injuries", "weather", "news", "transfers",
    "source_health", "collection_logs"
]

PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Kronos Data Hub - Durum</title>
<style>
body { font-family: -apple-system, sans-serif; background:#0b0f14; color:#e6edf3; padding:20px; }
h1 { color:#58a6ff; }
table { width:100%; border-collapse:collapse; margin-top:16px; }
td, th { padding:8px 12px; border-bottom:1px solid #21262d; text-align:left; }
.ok { color:#3fb950; font-weight:bold; }
.zero { color:#8b949e; }
.badge { background:#1f6feb; padding:2px 8px; border-radius:10px; font-size:12px; }
</style>
</head>
<body>
<h1>Kronos Data Hub</h1>
<p>Son kontrol: {{ now }} — <span class="badge">calisiyor</span></p>
<p><a href="/collect" style="background:#238636;color:white;padding:10px 16px;border-radius:6px;text-decoration:none;font-weight:bold;">Veri Topla (calistir)</a></p>
{% if collect_result %}
<pre style="background:#161b22;padding:12px;border-radius:6px;overflow-x:auto;font-size:12px;">{{ collect_result }}</pre>
{% endif %}
<table>
<tr><th>Tablo</th><th>Kayit Sayisi</th></tr>
{% for t, c in counts.items() %}
<tr><td>{{ t }}</td><td class="{{ 'ok' if c > 0 else 'zero' }}">{{ c }}</td></tr>
{% endfor %}
</table>
<p style="margin-top:20px;color:#8b949e;font-size:13px;">
API uc noktalari: <code>/health</code> · <code>/stats</code> · <code>/sources</code> · <code>/collect</code> · <code>/match_data</code>
</p>
</body>
</html>
"""


def get_counts():
    counts = {}
    for t in TABLES:
        try:
            row = db.fetch_one(f"SELECT COUNT(*) as c FROM {t}")
            counts[t] = row["c"] if row else 0
        except Exception:
            counts[t] = 0
    return counts


@app.route("/")
def dashboard():
    counts = get_counts()
    return render_template_string(
        PAGE_TEMPLATE, counts=counts, now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        collect_result=None
    )


@app.route("/collect")
def collect():
    result = subprocess.run(
        "python3 main.py --mode collect --source all",
        shell=True, capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__))
    )
    output = result.stdout + "\n" + result.stderr
    counts = get_counts()

    # DUZELTME (Drive kalicilik): veri toplama bittiginde guncel dosyayi
    # Drive'a yukle, boylece bir sonraki restart'ta veri kaybolmaz.
    upload_db_to_drive(DB_PATH)

    return render_template_string(
        PAGE_TEMPLATE, counts=counts, now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        collect_result=output
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat(), "version": "1.1.0"})


@app.route("/stats")
def stats():
    return jsonify(get_counts())


@app.route("/sources")
def sources():
    try:
        s = source_manager.get_all_sources()
        return jsonify({"count": len(s), "sources": list(s.keys())})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _find_team(name):
    if not name:
        return None
    row = db.fetch_one("SELECT * FROM teams WHERE lower(name) = lower(?)", (name,))
    if row:
        return row
    row = db.fetch_one(
        "SELECT * FROM teams WHERE lower(name) LIKE lower(?) ORDER BY length(name) ASC LIMIT 1",
        (f"%{name}%",),
    )
    return row


def _recent_form(team_id, limit=5):
    rows = db.fetch_all(
        """
        SELECT home_team_id, away_team_id, home_goals, away_goals, match_date
        FROM matches
        WHERE (home_team_id = ? OR away_team_id = ?)
          AND home_goals IS NOT NULL AND away_goals IS NOT NULL
        ORDER BY match_date DESC
        LIMIT ?
        """,
        (team_id, team_id, limit),
    )
    recent_results, scored, conceded, streak = [], [], [], []
    for r in rows:
        is_home = r["home_team_id"] == team_id
        gf = r["home_goals"] if is_home else r["away_goals"]
        ga = r["away_goals"] if is_home else r["home_goals"]
        recent_results.append({"home_goals": r["home_goals"], "away_goals": r["away_goals"], "home": is_home})
        scored.append(gf)
        conceded.append(ga)
        streak.append("W" if gf > ga else ("D" if gf == ga else "L"))
    return recent_results, scored, conceded, streak


def _injury_count(team_id):
    return db.fetch_scalar(
        "SELECT COUNT(*) FROM injuries WHERE team_id = ? AND status = 'out'", (team_id,)
    ) or 0


def _latest_odds(home_id, away_id):
    row = db.fetch_one(
        """
        SELECT o.* FROM odds o
        JOIN matches m ON o.match_id = m.id
        WHERE m.home_team_id = ? AND m.away_team_id = ?
        ORDER BY o.timestamp DESC LIMIT 1
        """,
        (home_id, away_id),
    )
    if not row:
        return None
    return {"home": row["home_odds"], "draw": row["draw_odds"], "away": row["away_odds"]}


@app.route("/match_data")
def match_data():
    home_name = request.args.get("home", "")
    away_name = request.args.get("away", "")

    home = _find_team(home_name)
    away = _find_team(away_name)

    result = {
        "home_team_found": bool(home),
        "away_team_found": bool(away),
        "home_team_matched_name": home["name"] if home else None,
        "away_team_matched_name": away["name"] if away else None,
    }

    if not home or not away:
        result["warning"] = "Bir veya iki takim veritabaninda bulunamadi."
        return jsonify(result)

    match = {}
    if home.get("elo_rating"):
        match["home_elo"] = home["elo_rating"]
    if away.get("elo_rating"):
        match["away_elo"] = away["elo_rating"]

    h_recent, h_scored, h_conceded, h_streak = _recent_form(home["id"])
    a_recent, a_scored, a_conceded, a_streak = _recent_form(away["id"])
    if h_recent:
        match["home_recent_results"] = h_recent
        match["home_scored"] = h_scored
        match["home_conceded"] = h_conceded
        match["home_recent_streak"] = h_streak
    if a_recent:
        match["away_recent_results"] = a_recent
        match["away_scored"] = a_scored
        match["away_conceded"] = a_conceded
        match["away_recent_streak"] = a_streak

    match["home_injured_players"] = _injury_count(home["id"])
    match["away_injured_players"] = _injury_count(away["id"])

    odds = _latest_odds(home["id"], away["id"])
    if odds:
        match["odds"] = odds

    result["match_data"] = match
    result["data_completeness"] = {
        "elo": bool(home.get("elo_rating") and away.get("elo_rating")),
        "recent_form": bool(h_recent and a_recent),
        "odds": bool(odds),
        "injuries": True,
    }
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

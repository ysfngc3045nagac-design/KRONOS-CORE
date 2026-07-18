"""
KRONOS_DATA_HUB - Web Server
Bu dosya, veri toplama sistemini bir web sayfasi/API olarak disariya acar.
Render'da ayri bir Web Service olarak calistirilmak icin tasarlandi.
"""
import os
import subprocess
from datetime import datetime
from flask import Flask, jsonify, render_template_string, redirect
from database.sqlite_manager import SQLiteManager
from core.source_manager import SourceManager

app = Flask(__name__)

DB_PATH = os.environ.get("KRONOS_DB_PATH", "data/kronos.db")
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
API uc noktalari: <code>/health</code> · <code>/stats</code> · <code>/sources</code> · <code>/collect</code>
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
    return render_template_string(
        PAGE_TEMPLATE, counts=counts, now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        collect_result=output
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat(), "version": "1.0.0"})


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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

"""
KRONOS FastAPI web servisi.

NOT: Onceki ozette "FastAPI web servisi ve sohbet arayuzu" tamamlandi olarak
listelenmisti ama konusma boyunca bu dosyanin kodu hic paylasilmadi. Mevcut
KronosApplication (core.app) uzerine minimal ama calisir bir REST API
yazildi.

Calistirmak icin:
    pip install fastapi uvicorn --break-system-packages
    uvicorn interface.api:app --reload
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

from football_engine.core.app import KronosApplication
from football_engine.core.version import VERSION

app = FastAPI(title="KRONOS", version=VERSION)

kronos = KronosApplication()


class MatchRequest(BaseModel):
    id: str
    home_elo: float | None = 1500
    away_elo: float | None = 1500
    xg: float | None = 1.2
    xga: float | None = 1.2
    scored: list[int] | None = []
    conceded: list[int] | None = []
    recent_results: list[dict[str, Any]] | None = []
    odds: dict[str, float] | None = None
    extra: dict[str, Any] | None = None


@app.get("/health")
def health():
    return kronos.health()


@app.post("/analyze")
def analyze(payload: MatchRequest):

    match = payload.model_dump(exclude_none=True)

    extra = match.pop("extra", None) or {}
    match.update(extra)

    try:
        report = kronos.analyze(match)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return report


@app.get("/agents")
def agents():
    return {"agents": kronos.registry.names(), "count": kronos.registry.count()}

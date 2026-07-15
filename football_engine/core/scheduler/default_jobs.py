"""Varsayilan sistem gorevleri."""

from football_engine.core.scheduler.job import Job


def cleanup_reports():
    return {"status": "ok", "message": "Rapor temizleme tamamlandi."}


def refresh_cache():
    return {"status": "ok", "message": "Onbellek yenilendi."}


DEFAULT_JOBS = [
    Job(name="cleanup_reports", handler=cleanup_reports),
    Job(name="refresh_cache", handler=refresh_cache),
]

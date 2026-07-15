"""
orchestration/scheduler.py

Basit, thread tabanlı bir zamanlayıcı. FastAPI'nin ana thread'ini
BLOKLAMAMASI için ayrı bir arka plan thread'inde çalışır.

Not (önemli kısıtlama): Render'ın ücretsiz planı, servis ~15 dakika
kullanılmadığında "uykuya" geçiriyor. Uykudayken bu zamanlayıcı da durur -
sadece servis biri tarafından ziyaret edilip uyandığında tekrar çalışır.
Yani "her saat başı" demek, "servis o an ayaktaysa her saat başı" demektir.
"""

import threading
import time
from typing import Callable


class Scheduler:
    def __init__(self):
        self._jobs: list[dict] = []
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def add_interval_job(self, name: str, interval_seconds: int, callback: Callable) -> None:
        self._jobs.append(
            {"name": name, "interval": interval_seconds, "callback": callback, "last_run": 0.0}
        )

    def start(self) -> None:
        if self._thread is not None:
            return  # zaten çalışıyor
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        while not self._stop.is_set():
            now = time.time()
            for job in self._jobs:
                if now - job["last_run"] >= job["interval"]:
                    job["last_run"] = now
                    try:
                        print(f"[Kronos Scheduler] Çalıştırılıyor: {job['name']}")
                        job["callback"]()
                    except Exception as exc:
                        print(f"[Kronos Scheduler] HATA ({job['name']}): {exc}")
            time.sleep(5)

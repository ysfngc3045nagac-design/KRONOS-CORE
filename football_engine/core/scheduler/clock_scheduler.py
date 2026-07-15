"""
Otomatik zamanlayici - iki ayri kullanim seklini birlestirir:
  - saat:dakika bazli gunluk gorevler (add_daily)
  - interval bazli tekrarlayan gorevler (add_interval)

NOT: `orchestration/scheduler.py`daki orijinal `run()` metodu, bir gorev
tetiklendiginde 60 saniye `time.sleep(60)` yapiyordu - ayni dakika icinde
baska bir gorev varsa onu kacirirdi. Bu versiyon, her tetiklenen gorevi
"bu dakika/interval icinde bir kez calisti" olarak isaretliyor, sabit
60 saniyelik bloklayici sleep kullanmiyor.
"""

from datetime import datetime
import time


class ClockScheduler:

    def __init__(self):
        self.daily_tasks = []
        self.interval_jobs = []

    def add_daily(self, name, hour, minute, callback, days=None):
        self.daily_tasks.append({
            "name": name, "hour": hour, "minute": minute,
            "callback": callback, "days": days, "last_run_minute": None,
        })

    def add_interval(self, seconds, func):
        self.interval_jobs.append({"interval": seconds, "last": 0, "func": func})

    def tick(self):

        now = datetime.now()
        current_minute_key = now.strftime("%Y%m%d%H%M")

        for task in self.daily_tasks:

            if task["days"] is not None and (now.isoweekday() % 7 + 1) not in task["days"]:
                continue

            if now.hour == task["hour"] and now.minute == task["minute"]:
                if task["last_run_minute"] != current_minute_key:
                    task["last_run_minute"] = current_minute_key
                    try:
                        task["callback"]()
                    except Exception as exc:
                        print(f"[KRONOS] Gunluk gorev hatasi ({task['name']}): {exc}")

        now_ts = time.time()

        for job in self.interval_jobs:
            if now_ts - job["last"] >= job["interval"]:
                try:
                    job["func"]()
                except Exception as exc:
                    print(f"[KRONOS] Interval gorev hatasi: {exc}")
                job["last"] = now_ts

    def run_forever(self, poll_seconds=1):
        while True:
            self.tick()
            time.sleep(poll_seconds)

"""
Analiz raporlarini diske saklar.

DUZELTME: dosya adi saniye hassasiyetindeydi (%Y%m%d_%H%M%S.json), ayni
saniyede iki rapor kaydedilirse birbirini ezerdi. Mikrosaniye + kisa bir
benzersiz sonek eklendi.
"""

from datetime import datetime
import uuid

from football_engine.core.storage.json_store import JsonStore


class ReportStore:

    def __init__(self):
        self.store = JsonStore("reports")

    def save_report(self, report):
        filename = (
            datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            + f"_{uuid.uuid4().hex[:6]}.json"
        )
        self.store.save(filename, report)
        return filename

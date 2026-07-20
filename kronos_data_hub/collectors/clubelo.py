"""KRONOS_DATA_HUB - ClubELO Collector"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
from .base_collector import BaseCollector

class ClubELOCollector(BaseCollector):
    def collect(self, team=None, **kwargs):
        start_time = datetime.now()
        self.stats["last_run"] = start_time.isoformat()
        try:
            if team:
                url = self._build_url("rankings", team=team)
            else:
                url = self._build_url("all_rankings")
            response = self._make_request(url)
            response.raise_for_status()
            records = self.parse_response(response)
            saved = self._save_elo_ratings(records)
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["successful"] += 1
            self.stats["records_collected"] += saved
            self._save_collection_log(f"clubelo_{team or 'all'}", "success", saved, "", elapsed)
            self._update_source_health(True, elapsed)
            return {"status": "success", "records": saved, "team": team, "duration_ms": elapsed}
        except Exception as e:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            self.stats["failed"] += 1
            self._save_collection_log(f"clubelo_{team or 'all'}", "failed", 0, str(e), elapsed)
            self._update_source_health(False)
            return {"status": "error", "error": str(e), "team": team}

    def parse_response(self, response):
        content = response.content.decode("utf-8", errors="ignore")
        records = self.csv_parser.parse(content)
        normalized = []
        for record in records:
            normalized.append({"rank": record.get("rank"), "club": record.get("club", ""),
                "country": record.get("country", ""), "level": record.get("level"), "elo": record.get("elo"),
                "from": record.get("from"), "to": record.get("to"), "source_id": self.source_id,
                "collected_at": datetime.now().isoformat()})
        return normalized

    def _save_elo_ratings(self, records):
        # DUZELTME: Onceki surumde her satirda UPDATE calistiriliyor, ama
        # etkilenen satir sayisi (rowcount) hic kontrol edilmiyordu - isim
        # eslesmese bile "saved" sayaci artiyordu, bu yuzden loglar "basarili"
        # gosteriyordu halbuki hicbir takima elo yazilmamis olabiliyordu.
        # Simdi: (1) rowcount kontrol ediliyor, (2) tam eslesme once denenir,
        # (3) olmazsa LIKE ile daha esnek deneniyor, (4) hicbiri tutmazsa bu
        # satir sayilmiyor ve kac tanesinin eslesmedigi loglaniyor.
        saved = 0
        unmatched = []
        for record in records:
            club = (record.get("club") or "").strip()
            if not club:
                continue
            cur = self.db.execute("UPDATE teams SET elo_rating = ? WHERE name = ? OR short_name = ?",
                (record.get("elo", 1500), club, club))
            if cur.rowcount == 0:
                cur = self.db.execute("UPDATE teams SET elo_rating = ? WHERE name LIKE ? OR short_name LIKE ?",
                    (record.get("elo", 1500), f"%{club}%", f"%{club}%"))
            if cur.rowcount and cur.rowcount > 0:
                saved += 1
            else:
                unmatched.append(club)
        if unmatched:
            self.logger.warning(f"ClubELO: {len(unmatched)} takim veritabaniyla eslesmedi (ornek: {unmatched[:5]})")
        return saved

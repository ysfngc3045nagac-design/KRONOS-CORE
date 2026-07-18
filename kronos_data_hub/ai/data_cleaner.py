"""KRONOS_DATA_HUB - Data Cleaner"""
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

class DataCleaner:
    def __init__(self):
        self.cleaning_rules = {"team_names": self._clean_team_name, "player_names": self._clean_player_name,
                               "dates": self._clean_date, "odds": self._clean_odds, "text": self._clean_text}

    def clean_record(self, record, rules=None):
        cleaned = dict(record)
        rules = rules or {}
        for field, rule in rules.items():
            if field in cleaned and cleaned[field] is not None:
                cleaner = self.cleaning_rules.get(rule)
                if cleaner:
                    cleaned[field] = cleaner(cleaned[field])
        return cleaned

    def _clean_team_name(self, name):
        if not name:
            return ""
        name = name.strip()
        replacements = {r"\bFC\b": "", r"\bCF\b": "", r"\bSC\b": "", r"\bAC\b": "", r"\bAS\b": "",
                        r"\bSS\b": "", r"\bUnited\b": "Utd", r"\bManchester\b": "Man"}
        for pattern, replacement in replacements.items():
            name = re.sub(pattern, replacement, name, flags=re.IGNORECASE)
        name = re.sub(r"\s+", " ", name).strip()
        return name

    def _clean_player_name(self, name):
        if not name:
            return ""
        name = name.strip()
        import unicodedata
        name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
        name = re.sub(r"[^\w\s\-\.]", "", name)
        return name.strip()

    def _clean_date(self, date_str):
        if not date_str:
            return ""
        date_str = str(date_str).strip()
        formats = ["%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d", "%d.%m.%Y", "%m/%d/%Y", "%Y%m%d",
                   "%a, %d %b %Y %H:%M:%S %z"]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except:
            pass
        return date_str

    def _clean_odds(self, odds):
        if odds is None:
            return None
        try:
            val = float(str(odds).replace(",", "."))
            if val < 1.01 or val > 1000:
                return None
            return round(val, 2)
        except (ValueError, TypeError):
            return None

    def _clean_text(self, text):
        if not text:
            return ""
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text)
        text = text.replace("\n", " ").replace("\t", " ")
        return text.strip()

    def remove_duplicates(self, records, key_fields):
        seen = set()
        unique = []
        for record in records:
            key = tuple(str(record.get(f, "")) for f in key_fields)
            if key not in seen:
                seen.add(key)
                unique.append(record)
        return unique

    def fill_missing_values(self, records, defaults):
        filled = []
        for record in records:
            cleaned = dict(record)
            for field, default in defaults.items():
                if field not in cleaned or cleaned[field] is None:
                    cleaned[field] = default
            filled.append(cleaned)
        return filled

    def validate_required_fields(self, record, required):
        missing = []
        for field in required:
            if field not in record or record[field] is None or record[field] == "":
                missing.append(field)
        return missing

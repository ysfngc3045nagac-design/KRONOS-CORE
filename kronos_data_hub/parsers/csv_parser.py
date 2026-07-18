"""KRONOS_DATA_HUB - CSV Parser"""
import csv
import io
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

class CSVParser:
    def __init__(self):
        self.errors = []

    def parse(self, data, delimiter=",", encoding="utf-8", has_header=True):
        try:
            if isinstance(data, bytes):
                data = data.decode(encoding)
            reader = csv.DictReader(io.StringIO(data), delimiter=delimiter) if has_header else csv.reader(io.StringIO(data), delimiter=delimiter)
            if has_header:
                return [self._clean_row(row) for row in reader]
            else:
                return [{f"col_{i}": v for i, v in enumerate(row)} for row in reader]
        except Exception as e:
            self.errors.append(f"CSV parse error: {e}")
            return []

    def _clean_row(self, row):
        cleaned = {}
        for key, value in row.items():
            if key is None:
                continue
            clean_key = key.strip().lower().replace(" ", "_")
            cleaned[clean_key] = self._convert_value(value)
        return cleaned

    def _convert_value(self, value):
        if value is None or value.strip() == "" or value.strip() == "NA":
            return None
        value = value.strip()
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False
        return value

    def parse_file(self, filepath, delimiter=",", encoding="utf-8"):
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return self.parse(f.read(), delimiter, encoding)
        except Exception as e:
            self.errors.append(f"File parse error: {e}")
            return []

    def to_dict_list(self, rows):
        return [self._clean_row(row) for row in rows]

    def get_column_stats(self, data, column):
        values = [row.get(column) for row in data if row.get(column) is not None]
        numeric = [v for v in values if isinstance(v, (int, float))]
        stats = {"total_rows": len(data), "non_null": len(values),
                 "null_count": len(data) - len(values), "unique_values": len(set(str(v) for v in values))}
        if numeric:
            stats["min"] = min(numeric)
            stats["max"] = max(numeric)
            stats["avg"] = sum(numeric) / len(numeric)
        return stats

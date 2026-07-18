"""KRONOS_DATA_HUB - JSON Parser"""
import json
import re
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

class JSONParser:
    def __init__(self):
        self.errors = []

    def parse(self, data, encoding="utf-8"):
        try:
            if isinstance(data, bytes):
                data = data.decode(encoding)
            return json.loads(data)
        except json.JSONDecodeError as e:
            self.errors.append(f"JSON parse error: {e}")
            return self._loose_parse(data)
        except Exception as e:
            self.errors.append(f"Unexpected error: {e}")
            return None

    def _loose_parse(self, data):
        fixed = data.replace("'", '"')
        fixed = re.sub(r',\s*}', '}', fixed)
        fixed = re.sub(r',\s*]', ']', fixed)
        try:
            return json.loads(fixed)
        except:
            return None

    def extract_nested(self, data, path, default=None):
        keys = path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    def flatten(self, data, parent_key="", sep="_"):
        items = []
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten(v, new_key, sep).items())
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                for i, item in enumerate(v):
                    items.extend(self.flatten(item, f"{new_key}{sep}{i}", sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def normalize_dates(self, data, date_fields, fmt="%Y-%m-%d"):
        result = dict(data)
        for field in date_fields:
            if field in result and result[field]:
                try:
                    dt = datetime.fromisoformat(str(result[field]).replace('Z', '+00:00'))
                    result[field] = dt.strftime(fmt)
                except:
                    pass
        return result

    def safe_get(self, data, key, default=None, cast_type=None):
        value = data.get(key, default)
        if value is None:
            return default
        if cast_type:
            try:
                if cast_type == bool and isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return cast_type(value)
            except (ValueError, TypeError):
                return default
        return value

    def validate_schema(self, data, required_fields):
        missing = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing.append(field)
        return missing

"""KRONOS_DATA_HUB - Backup Manager"""
import os
import shutil
import gzip
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

class BackupManager:
    def __init__(self, db_path, backup_dir="backups", max_backups=30, compress=True):
        self.db_path = db_path
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        self.compress = compress
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, label=None):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        label_suffix = f"_{label}" if label else ""
        if self.compress:
            backup_name = f"kronos_{timestamp}{label_suffix}.db.gz"
            backup_path = self.backup_dir / backup_name
            self._create_compressed_backup(backup_path)
        else:
            backup_name = f"kronos_{timestamp}{label_suffix}.db"
            backup_path = self.backup_dir / backup_name
            self._create_plain_backup(backup_path)
        self._rotate_backups()
        return str(backup_path)

    def _create_plain_backup(self, backup_path):
        source = sqlite3.connect(self.db_path)
        backup = sqlite3.connect(str(backup_path))
        with backup:
            source.backup(backup)
        source.close()
        backup.close()

    def _create_compressed_backup(self, backup_path):
        temp_path = self.backup_dir / f"temp_{datetime.now().timestamp()}.db"
        self._create_plain_backup(temp_path)
        with open(temp_path, 'rb') as f_in:
            with gzip.open(backup_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        temp_path.unlink()

    def restore_backup(self, backup_path, target_path=None):
        backup_path = Path(backup_path)
        target = target_path or self.db_path
        if not backup_path.exists():
            raise FileNotFoundError(f"Yedek bulunamadi: {backup_path}")
        if os.path.exists(target):
            safety_backup = f"{target}.safety_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(target, safety_backup)
        if backup_path.suffix == '.gz':
            self._restore_compressed(backup_path, target)
        else:
            shutil.copy2(str(backup_path), target)
        return target

    def _restore_compressed(self, backup_path, target):
        with gzip.open(backup_path, 'rb') as f_in:
            with open(target, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

    def list_backups(self):
        backups = []
        for file_path in sorted(self.backup_dir.glob("kronos_*.db*"), reverse=True):
            stat = file_path.stat()
            backups.append({
                "filename": file_path.name, "path": str(file_path),
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "compressed": file_path.suffix == '.gz'
            })
        return backups

    def _rotate_backups(self):
        backups = self.list_backups()
        if len(backups) > self.max_backups:
            to_delete = backups[self.max_backups:]
            for backup in to_delete:
                Path(backup["path"]).unlink(missing_ok=True)

    def delete_backup(self, backup_name):
        backup_path = self.backup_dir / backup_name
        if backup_path.exists():
            backup_path.unlink()
            return True
        return False

    def get_backup_info(self, backup_path):
        path = Path(backup_path)
        stat = path.stat()
        return {
            "filename": path.name, "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "compressed": path.suffix == '.gz'
        }

    def auto_backup_if_needed(self, interval_hours=24):
        backups = self.list_backups()
        if not backups:
            return self.create_backup("auto")
        last_backup_time = datetime.fromisoformat(backups[0]["created"])
        if datetime.now() - last_backup_time > timedelta(hours=interval_hours):
            return self.create_backup("auto")
        return None

    def export_table(self, table_name, output_path, format="csv"):
        import csv
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        headers = [description[0] for description in cursor.description]
        if format == "csv":
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
        elif format == "json":
            import json
            data = [dict(row) for row in rows]
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        conn.close()
        return output_path

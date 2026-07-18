"""KRONOS_DATA_HUB - SQLite Manager"""
import sqlite3
import threading
import os
import json
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from .models import DatabaseSchema

class SQLiteManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path: str = "data/kronos.db"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = "data/kronos.db"):
        if self._initialized:
            return
        self.db_path = db_path
        self._local = threading.local()
        self._pool_lock = threading.Lock()
        self._connection_pool = []
        self._max_pool_size = 5
        self._pool_size = 0
        # DUZELTME: db_path ":memory:" ise veya sadece dosya adiysa (klasor
        # kismi bos string donuyor), os.makedirs("") FileNotFoundError verirdi.
        # Sadece gercek bir klasor bilesenimiz varsa olustur.
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._init_database()
        self._initialized = True

    def _init_database(self):
        with self.get_connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=-64000")
            conn.execute("PRAGMA temp_store=MEMORY")
            DatabaseSchema.create_all(conn)

    def _create_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @contextmanager
    def get_connection(self):
        conn = None
        try:
            if hasattr(self._local, 'connection') and self._local.connection:
                conn = self._local.connection
            else:
                with self._pool_lock:
                    if self._connection_pool:
                        conn = self._connection_pool.pop()
                    else:
                        conn = self._create_connection()
                        self._pool_size += 1
                self._local.connection = conn
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn and not hasattr(self._local, 'in_transaction'):
                with self._pool_lock:
                    if len(self._connection_pool) < self._max_pool_size:
                        self._connection_pool.append(conn)
                    else:
                        conn.close()
                        self._pool_size -= 1
                if hasattr(self._local, 'connection'):
                    del self._local.connection

    @contextmanager
    def transaction(self):
        with self.get_connection() as conn:
            self._local.in_transaction = True
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                del self._local.in_transaction

    def execute(self, query, params=()):
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor

    def execute_many(self, query, params_list):
        with self.transaction() as conn:
            cursor = conn.executemany(query, params_list)
            return cursor

    def fetch_one(self, query, params=()):
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def fetch_all(self, query, params=()):
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def fetch_scalar(self, query, params=()):
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            return row[0] if row else None

    def insert(self, table, data, conflict_resolution="IGNORE"):
        if not data:
            return None
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        query = f"INSERT OR {conflict_resolution} INTO {table} ({columns}) VALUES ({placeholders})"
        with self.get_connection() as conn:
            cursor = conn.execute(query, tuple(data.values()))
            conn.commit()
            return cursor.lastrowid

    def insert_many(self, table, data_list, conflict_resolution="IGNORE"):
        if not data_list:
            return 0
        columns = ", ".join(data_list[0].keys())
        placeholders = ", ".join(["?"] * len(data_list[0]))
        query = f"INSERT OR {conflict_resolution} INTO {table} ({columns}) VALUES ({placeholders})"
        params = [tuple(d.values()) for d in data_list]
        with self.transaction() as conn:
            cursor = conn.executemany(query, params)
            return cursor.rowcount

    def update(self, table, data, where, where_params):
        if not data:
            return 0
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        params = tuple(data.values()) + where_params
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount

    def delete(self, table, where, params=()):
        query = f"DELETE FROM {table} WHERE {where}"
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount

    def table_exists(self, table_name):
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        return self.fetch_scalar(query, (table_name,)) is not None

    def get_table_info(self, table_name):
        return self.fetch_all(f"PRAGMA table_info({table_name})")

    def get_row_count(self, table_name):
        return self.fetch_scalar(f"SELECT COUNT(*) FROM {table_name}") or 0

    def vacuum(self):
        with self.get_connection() as conn:
            conn.execute("VACUUM")

    def close_all(self):
        with self._pool_lock:
            for conn in self._connection_pool:
                conn.close()
            self._connection_pool.clear()
            self._pool_size = 0

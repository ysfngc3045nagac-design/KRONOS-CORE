"""KRONOS_DATA_HUB - Scheduler"""
import threading
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging

@dataclass
class ScheduledTask:
    id: str
    name: str
    func: Callable
    interval_seconds: int
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    enabled: bool = True
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)

class Scheduler:
    def __init__(self):
        self.tasks = {}
        self._thread = None
        self._running = False
        self._lock = threading.Lock()
        self.logger = logging.getLogger("scheduler")

    def add_task(self, task_id, name, func, interval_minutes, *args, **kwargs):
        interval = interval_minutes * 60
        task = ScheduledTask(id=task_id, name=name, func=func, interval_seconds=interval,
                              next_run=datetime.now(), args=args, kwargs=kwargs)
        with self._lock:
            self.tasks[task_id] = task
        self.logger.info(f"Task added: {name} (every {interval_minutes} min)")
        return task

    def remove_task(self, task_id):
        with self._lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                return True
            return False

    def enable_task(self, task_id):
        with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id].enabled = True
                return True
            return False

    def disable_task(self, task_id):
        with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id].enabled = False
                return True
            return False

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self.logger.info("Scheduler started")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self.logger.info("Scheduler stopped")

    def _run_loop(self):
        while self._running:
            now = datetime.now()
            with self._lock:
                tasks_to_run = [t for t in self.tasks.values() if t.enabled and t.next_run and now >= t.next_run]
            for task in tasks_to_run:
                self._execute_task(task)
            time.sleep(10)

    def _execute_task(self, task):
        self.logger.info(f"Executing task: {task.name}")
        try:
            task.func(*task.args, **task.kwargs)
            task.run_count += 1
            task.error_count = max(0, task.error_count - 1)
        except Exception as e:
            self.logger.error(f"Task {task.name} failed: {e}")
            task.error_count += 1
            if task.error_count >= 5:
                task.enabled = False
                self.logger.warning(f"Task {task.name} disabled due to errors")
        finally:
            task.last_run = datetime.now()
            task.next_run = datetime.now() + timedelta(seconds=task.interval_seconds)

    def run_now(self, task_id):
        with self._lock:
            if task_id not in self.tasks:
                return False
            task = self.tasks[task_id]
        self._execute_task(task)
        return True

    def get_status(self):
        with self._lock:
            tasks_status = []
            for task in self.tasks.values():
                tasks_status.append({
                    "id": task.id, "name": task.name, "enabled": task.enabled,
                    "interval_minutes": task.interval_seconds // 60,
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "next_run": task.next_run.isoformat() if task.next_run else None,
                    "run_count": task.run_count, "error_count": task.error_count
                })
            return {"running": self._running, "task_count": len(self.tasks), "tasks": tasks_status}

    def get_task_history(self, task_id, limit=10):
        return []

"""KRONOS_DATA_HUB - Retry Manager"""
import time
import random
import threading
from enum import Enum
from typing import Callable, Optional, Type, List, Dict, Any
from dataclasses import dataclass, field
from functools import wraps

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: List[Type[Exception]] = field(default_factory=lambda: [ConnectionError, TimeoutError, OSError])

    def calculate_delay(self, attempt):
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)
        if self.jitter:
            delay *= random.uniform(0.75, 1.25)
        return delay

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    half_open_max_calls: int = 3
    success_threshold: int = 2

class CircuitBreaker:
    def __init__(self, config):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.half_open_calls = 0
        self._lock = threading.Lock()

    def can_execute(self):
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            if self.state == CircuitState.OPEN:
                if time.monotonic() - self.last_failure_time >= self.config.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    self.success_count = 0
                    return True
                return False
            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls < self.config.half_open_max_calls:
                    self.half_open_calls += 1
                    return True
                return False
            return False

    def record_success(self):
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
            elif self.state == CircuitState.CLOSED:
                self.failure_count = max(0, self.failure_count - 1)

    def record_failure(self):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.monotonic()
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
            elif self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN

    def get_status(self):
        with self._lock:
            return {
                "state": self.state.value, "failure_count": self.failure_count,
                "success_count": self.success_count, "half_open_calls": self.half_open_calls,
                "last_failure": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.last_failure_time)) if self.last_failure_time else None
            }

class CircuitBreakerOpenError(Exception):
    pass

class RetryManager:
    def __init__(self):
        self._breakers = {}
        self._configs = {}
        self._breaker_configs = {}
        self._lock = threading.Lock()
        self._stats = {"total_calls": 0, "successful_calls": 0, "failed_calls": 0, "retried_calls": 0, "circuit_blocked": 0}

    def register_source(self, source_id, retry_config=None, breaker_config=None):
        with self._lock:
            self._configs[source_id] = retry_config or RetryConfig()
            self._breaker_configs[source_id] = breaker_config or CircuitBreakerConfig()
            self._breakers[source_id] = CircuitBreaker(self._breaker_configs[source_id])

    def execute(self, source_id, func, *args, **kwargs):
        with self._lock:
            self._stats["total_calls"] += 1
            if source_id not in self._breakers:
                self.register_source(source_id)
            breaker = self._breakers[source_id]
            config = self._configs[source_id]
        if not breaker.can_execute():
            self._stats["circuit_blocked"] += 1
            raise CircuitBreakerOpenError(f"Circuit breaker OPEN for source: {source_id}")
        last_exception = None
        for attempt in range(config.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                breaker.record_success()
                self._stats["successful_calls"] += 1
                return result
            except Exception as e:
                last_exception = e
                if not any(isinstance(e, exc_type) for exc_type in config.retryable_exceptions):
                    breaker.record_failure()
                    self._stats["failed_calls"] += 1
                    raise
                if attempt < config.max_retries:
                    self._stats["retried_calls"] += 1
                    delay = config.calculate_delay(attempt)
                    time.sleep(delay)
                else:
                    break
        breaker.record_failure()
        self._stats["failed_calls"] += 1
        raise last_exception

    def execute_async(self, source_id, func, *args, **kwargs):
        return self.execute(source_id, func, *args, **kwargs)

    def get_source_status(self, source_id):
        with self._lock:
            if source_id not in self._breakers:
                return {"error": "Source not registered"}
            return {"source_id": source_id, **self._breakers[source_id].get_status(),
                    "max_retries": self._configs[source_id].max_retries,
                    "base_delay": self._configs[source_id].base_delay}

    def get_all_status(self):
        with self._lock:
            return {source_id: {**breaker.get_status(), "max_retries": self._configs[source_id].max_retries}
                    for source_id, breaker in self._breakers.items()}

    def get_stats(self):
        with self._lock:
            return dict(self._stats)

    def reset_source(self, source_id):
        with self._lock:
            if source_id in self._breaker_configs:
                self._breakers[source_id] = CircuitBreaker(self._breaker_configs[source_id])

    def reset_all(self):
        with self._lock:
            for source_id in self._breakers:
                self._breakers[source_id] = CircuitBreaker(self._breaker_configs[source_id])

def with_retry(source_id, retry_manager, max_retries=3, base_delay=1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return retry_manager.execute(source_id, func, *args, **kwargs)
        return wrapper
    return decorator

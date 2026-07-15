"""Calistirilabilir gorev."""

from dataclasses import dataclass
from typing import Callable, Any


@dataclass
class Job:

    name: str
    handler: Callable[..., Any]
    enabled: bool = True

    def run(self, *args, **kwargs):
        if not self.enabled:
            return None
        return self.handler(*args, **kwargs)

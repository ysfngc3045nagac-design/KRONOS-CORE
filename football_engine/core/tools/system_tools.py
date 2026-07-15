"""Sistem bilgisi araclari"""

import os
import platform
import socket
from football_engine.core.tools.registry import tool_registry


@tool_registry.register(
    name="system_info", description="Calisan sistem hakkinda temel bilgi dondurur.",
    parameters={"type": "object", "properties": {}, "required": []},
)
def system_info():
    return {
        "platform": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "hostname": socket.gethostname(),
    }


@tool_registry.register(
    name="environment_variable", description="Bir ortam degiskenini okur.",
    parameters={"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
)
def environment_variable(name: str):
    return os.getenv(name)


@tool_registry.register(
    name="working_directory", description="Calisma dizinini dondurur.",
    parameters={"type": "object", "properties": {}, "required": []},
)
def working_directory():
    return os.getcwd()


@tool_registry.register(
    name="list_environment", description="Tanimli ortam degiskenlerinin isimlerini dondurur.",
    parameters={"type": "object", "properties": {}, "required": []},
)
def list_environment():
    return sorted(os.environ.keys())

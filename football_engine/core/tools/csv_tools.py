"""
CSV araclari

DUZELTME: write_csv/append_csv fieldnames'i sadece ilk satirdan aliyordu.
Satirlar arasinda farkli key varsa ValueError verirdi. Artik tum satirlarin
key'lerinin BIRLESIMI (union) kullaniliyor, extrasaction='ignore' ile de
guvenceye aliniyor. append_csv artik mevcut dosyanin header'ini okuyup
kontrol ediyor.
"""

import csv
from pathlib import Path
from football_engine.core.tools.registry import tool_registry


@tool_registry.register(
    name="read_csv", description="CSV dosyasini okur.",
    parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
)
def read_csv(path: str):
    file = Path(path)
    if not file.exists():
        return []
    with open(file, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _all_fieldnames(rows: list) -> list:
    fields = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                fields.append(key)
    return fields


@tool_registry.register(
    name="write_csv", description="CSV dosyasi olusturur.",
    parameters={
        "type": "object",
        "properties": {"path": {"type": "string"}, "rows": {"type": "array"}},
        "required": ["path", "rows"],
    },
)
def write_csv(path: str, rows: list):

    if not rows:
        return "Bos veri."

    file = Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = _all_fieldnames(rows)

    with open(file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return "OK"


@tool_registry.register(
    name="append_csv", description="CSV dosyasina satir ekler.",
    parameters={
        "type": "object",
        "properties": {"path": {"type": "string"}, "row": {"type": "object"}},
        "required": ["path", "row"],
    },
)
def append_csv(path: str, row: dict):

    file = Path(path)
    exists = file.exists()

    fieldnames = list(row.keys())

    if exists:
        with open(file, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header:
                # var olan header'i koru, yeni key'leri sona ekle
                fieldnames = header + [k for k in row.keys() if k not in header]

    with open(file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerow(row)

    return "OK"

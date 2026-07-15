"""JSON rapor disa aktarma."""

import json
from pathlib import Path


class ReportExporter:

    def export(self, report, filename):
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(report, file, indent=2, ensure_ascii=False)
        return str(path)

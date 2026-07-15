"""Analiz raporu olusturucu."""

from datetime import datetime


class ReportBuilder:

    def build(self, match, analysis):
        return {
            "created_at": datetime.utcnow().isoformat(),
            "match": match,
            "analysis": analysis,
            "overall_score": analysis.get("overall_score", 0),
            "confidence": analysis.get("confidence", 0),
            "risk": analysis.get("risk", 0),
            "decision": analysis.get("decision", ""),
            "details": analysis.get("details", []),
        }

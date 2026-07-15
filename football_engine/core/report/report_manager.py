"""Merkezi rapor yoneticisi."""

from football_engine.core.report.report_builder import ReportBuilder
from football_engine.core.report.report_exporter import ReportExporter
from football_engine.core.report.report_history import ReportHistory


class ReportManager:

    def __init__(self):
        self.builder = ReportBuilder()
        self.exporter = ReportExporter()
        self.history = ReportHistory(limit=500)

    def create(self, match, analysis, filename):
        report = self.builder.build(match, analysis)
        self.exporter.export(report, filename)
        self.history.add(report)
        return report

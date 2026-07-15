"""Rapor dogrulama."""

from football_engine.core.validation.validator import Validator


class ReportValidator(Validator):

    REQUIRED = ["overall_score", "decision"]

    def validate(self, report):
        return self.require(report, self.REQUIRED)

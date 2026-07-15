"""Takim dogrulama."""

from football_engine.core.validation.validator import Validator


class TeamValidator(Validator):

    REQUIRED = ["id", "name"]

    def validate(self, team):
        return self.require(team, self.REQUIRED)

"""Mac verisi dogrulama."""

from football_engine.core.validation.validator import Validator


class MatchValidator(Validator):

    REQUIRED = ["id", "home", "away", "date"]

    def validate(self, match):
        return self.require(match, self.REQUIRED)

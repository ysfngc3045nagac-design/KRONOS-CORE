"""
KRONOS Logger (tek, birlestirilmis surum)

Not: iki ayri KronosLogger tanimi vardi (staticmethod + global basicConfig,
ve instance tabanli + kendi handler'ini kuran). Instance tabanli olani sectim
cunku tekrar tekrar handler eklenmesini onluyor.
"""

import logging


class KronosLogger:

    def __init__(self, name: str = "KRONOS"):

        self.logger = logging.getLogger(name)

        if not self.logger.handlers:

            handler = logging.StreamHandler()

            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(message)s"
            )

            handler.setFormatter(formatter)

            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def exception(self, message):
        self.logger.exception(message)

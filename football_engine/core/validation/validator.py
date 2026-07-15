"""Merkezi veri dogrulayici."""


class Validator:

    def require(self, data, fields):
        return [f for f in fields if f not in data]

    def valid(self, data, fields):
        return len(self.require(data, fields)) == 0

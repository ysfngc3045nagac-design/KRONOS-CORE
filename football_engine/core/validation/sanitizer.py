"""Basit giris temizleyici."""


class Sanitizer:

    @staticmethod
    def clean(text):
        if not isinstance(text, str):
            return text
        return text.replace("<", "").replace(">", "").strip()

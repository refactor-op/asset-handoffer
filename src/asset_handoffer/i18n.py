import locale
from importlib import resources
import yaml


def detect_language() -> str:
    lang, _ = locale.getdefaultlocale()
    if lang and lang.startswith("zh"):
        return "zh-CN"
    return "en-US"


class Messages:
    def __init__(self, language: str = None):
        self.language = language or detect_language()
        self.messages: dict[str, str] = {}

        try:
            base = resources.files("asset_handoffer").joinpath("locales")
            with resources.as_file(base / f"{self.language}.yaml") as src:
                self.messages = yaml.safe_load(src.read_text(encoding="utf-8")) or {}
        except Exception:
            pass

    def t(self, key: str, **kwargs) -> str:
        s = self.messages.get(key, key)
        try:
            return s.format(**kwargs)
        except Exception:
            return s

"""国际化支持"""

from importlib import resources
from pathlib import Path
import yaml


class Messages:
    """本地化消息管理"""
    
    def __init__(self, language: str, messages_path: Path | None = None):
        self.language = language
        self.messages: dict[str, str] = {}
        
        if messages_path:
            p = Path(messages_path)
            if p.is_dir():
                f = p / f"{language}.yaml"
            else:
                f = p
            if f.exists():
                with open(f, "r", encoding="utf-8") as fh:
                    self.messages = yaml.safe_load(fh) or {}
                return
        
        try:
            base = resources.files("asset_handoffer").joinpath("locales")
            candidate = base / f"{language}.yaml"
            with resources.as_file(candidate) as src:
                with open(src, "r", encoding="utf-8") as fh:
                    self.messages = yaml.safe_load(fh) or {}
        except Exception:
            pass
    
    def t(self, key: str, default: str | None = None, **kwargs) -> str:
        s = self.messages.get(key, default or key)
        try:
            return s.format(**kwargs)
        except Exception:
            return s


def get_messages(language: str = "zh-CN") -> Messages:
    return Messages(language)

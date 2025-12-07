from importlib import resources
import yaml


class Messages:
    def __init__(self, language: str = "zh-CN"):
        self.language = language
        self.messages: dict[str, str] = {}
        
        for pkg in ["asset_handoffer.core", "asset_handoffer"]:
            try:
                base = resources.files(pkg).joinpath("locales")
                with resources.as_file(base / f"{language}.yaml") as src:
                    with open(src, "r", encoding="utf-8") as f:
                        self.messages = yaml.safe_load(f) or {}
                        return
            except Exception:
                continue
    
    def t(self, key: str, **kwargs) -> str:
        s = self.messages.get(key, key)
        try:
            return s.format(**kwargs)
        except Exception:
            return s

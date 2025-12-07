from pathlib import Path
from .protocols import ParsedResult
from .exceptions import ProcessError
from .i18n import Messages


class PathGenerator:
    def __init__(self, default_template: str, asset_root: str, messages: Messages = None):
        self.default_template = default_template
        self.asset_root = asset_root
        self.messages = messages or Messages()
    
    def generate(self, parsed: ParsedResult, repo_base: Path) -> Path:
        template = parsed.path_template if parsed.path_template else self.default_template
        
        try:
            rel_path = template.format(**parsed.groups)
        except KeyError as e:
            raise ProcessError(self.messages.t(
                'process.template_undefined_field',
                field=str(e).strip("'"),
                available=', '.join(parsed.groups.keys())
            ))
        
        full_path = repo_base / self.asset_root / rel_path
        
        if rel_path.endswith(('.', '/')):
            full_path.mkdir(parents=True, exist_ok=True)
            return full_path / parsed.original_name
        
        full_path.parent.mkdir(parents=True, exist_ok=True)
        return full_path

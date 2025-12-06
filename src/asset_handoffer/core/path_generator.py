"""路径生成器"""

from pathlib import Path
from ..parsers import ParsedFilename
from ..exceptions import ProcessError
from ..i18n import Messages


class PathGenerator:
    """路径生成器"""
    
    def __init__(self, path_template: str, asset_root: str, messages: Messages = None):
        self.path_template = path_template
        self.asset_root = asset_root
        self.messages = messages or Messages('zh-CN')
    
    def generate(self, parsed: ParsedFilename, repo_base: Path) -> Path:
        try:
            rel_dir = self.path_template.format(**parsed.groups)
        except KeyError as e:
            available = ', '.join(parsed.groups.keys())
            raise ProcessError(
                self.messages.t('process.template_undefined_field',
                              field=str(e).strip("'"),
                              available=available)
            )
        
        full_dir = repo_base / self.asset_root / rel_dir
        full_path = full_dir / parsed.original_name
        
        return full_path

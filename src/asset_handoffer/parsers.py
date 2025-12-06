"""文件名解析器"""

import re
from dataclasses import dataclass
from typing import Pattern

from .exceptions import ParseError
from .i18n import Messages


@dataclass
class ParsedFilename:
    """解析后的文件名信息"""
    original_name: str
    groups: dict[str, str]
    
    def __getitem__(self, key: str) -> str:
        return self.groups[key]
    
    def get(self, key: str, default: str = '') -> str:
        return self.groups.get(key, default)
    
    @property
    def extension(self) -> str:
        return self.groups.get('ext') or self.groups.get('extension', '')


class FilenameParser:
    """文件名解析器"""
    
    def __init__(self, pattern: str, messages: Messages = None):
        self.messages = messages or Messages('zh-CN')
        
        try:
            self.pattern: Pattern = re.compile(pattern)
        except re.error as e:
            raise ParseError(self.messages.t('parse.invalid_pattern', error=str(e)))
        
        groups = set(self.pattern.groupindex.keys())
        if not ('ext' in groups or 'extension' in groups):
            raise ParseError(self.messages.t('parse.missing_ext_group'))
    
    def parse(self, filename: str) -> ParsedFilename:
        match = self.pattern.match(filename)
        
        if not match:
            raise ParseError(self.messages.t('parse.filename_not_match', filename=filename))
        
        return ParsedFilename(
            original_name=filename,
            groups=match.groupdict()
        )

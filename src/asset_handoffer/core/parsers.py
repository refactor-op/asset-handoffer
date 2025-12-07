import re
from dataclasses import dataclass
from typing import Pattern
from .exceptions import ParseError
from .i18n import Messages


@dataclass
class NamingRule:
    pattern: Pattern
    path_template: str
    example: str = ""


@dataclass
class ParsedFilename:
    original_name: str
    groups: dict[str, str]
    path_template: str = ""


class FilenameParser:
    def __init__(self, pattern: str = None, messages: Messages = None, *, rules: list[dict] = None):
        self.messages = messages or Messages()
        self.rules: list[NamingRule] = []
        
        if rules:
            for rule in rules:
                self._add_rule(rule['pattern'], rule.get('path_template', ''), rule.get('example', ''))
        elif pattern:
            self._add_rule(pattern, '', '')
    
    def _add_rule(self, pattern: str, path_template: str, example: str):
        try:
            compiled = re.compile(pattern)
        except re.error as e:
            raise ParseError(self.messages.t('parse.invalid_pattern', error=str(e)))
        
        if not ('ext' in compiled.groupindex or 'extension' in compiled.groupindex):
            raise ParseError(self.messages.t('parse.missing_ext_group'))
        
        self.rules.append(NamingRule(pattern=compiled, path_template=path_template, example=example))
    
    def parse(self, filename: str) -> ParsedFilename:
        for rule in self.rules:
            match = rule.pattern.match(filename)
            if match:
                return ParsedFilename(
                    original_name=filename,
                    groups=match.groupdict(),
                    path_template=rule.path_template
                )
        
        examples = [r.example for r in self.rules if r.example]
        msg = self.messages.t('parse.filename_not_match', filename=filename)
        if examples:
            msg += "\n" + self.messages.t('parse.examples', examples=', '.join(examples))
        raise ParseError(msg)

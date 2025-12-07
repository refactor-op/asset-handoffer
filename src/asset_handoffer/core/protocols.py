from pathlib import Path
from typing import Protocol


class ParsedResult(Protocol):
    @property
    def original_name(self) -> str: ...
    
    @property
    def groups(self) -> dict[str, str]: ...
    
    @property
    def path_template(self) -> str: ...


class IParser(Protocol):
    def parse(self, filename: str) -> ParsedResult: ...


class IPathGenerator(Protocol):
    def generate(self, parsed: ParsedResult, repo_base: Path) -> Path: ...

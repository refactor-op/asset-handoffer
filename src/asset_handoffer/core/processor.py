import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable
from dataclasses import dataclass

from .config import Config
from .git_repo import GitRepo
from .parsers import FilenameParser
from .path_generator import PathGenerator as DefaultPathGenerator
from .protocols import IParser, IPathGenerator
from .exceptions import GitError, ProcessError, ParseError


@dataclass
class ProcessResult:
    success: bool
    source_path: Path
    target_path: Optional[Path] = None
    error: Optional[str] = None


class FileProcessor:
    def __init__(
        self, 
        config: Config,
        *,
        parser: Optional[IParser] = None,
        path_generator: Optional[IPathGenerator] = None,
        on_message: Optional[Callable[[str], None]] = None
    ):
        self.config = config
        self.messages = config.messages
        self._output = on_message or print
        
        self.parser = parser or FilenameParser(rules=config.naming_rules, messages=self.messages)
        self.path_gen = path_generator or DefaultPathGenerator(
            config.path_template, config.asset_root, self.messages
        )
        self.repo = GitRepo(config.repo, self.messages, config.git_token)
    
    def process(self, file_path: Path) -> ProcessResult:
        try:
            if not self.repo.exists():
                raise ProcessError(self.messages.t('process.repo_not_exists'))
            
            try:
                parsed = self.parser.parse(file_path.name)
            except ParseError as e:
                raise ProcessError(
                    self.messages.t('process.filename_error',
                                  error=str(e),
                                  example=self.config.naming_example)
                )
            
            target_path = self.path_gen.generate(parsed, self.config.repo)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(file_path), str(target_path))
            
            try:
                self.repo.pull()
                self.repo.add(target_path)
                commit_msg = self.config.git_commit_template.format(**parsed.groups)
                self.repo.commit(commit_msg)
                self.repo.push()
            except GitError as e:
                self._handle_git_failure(target_path, file_path, e)
                return ProcessResult(success=False, source_path=file_path, error=str(e))
            
            self._output(self.messages.t('process.success', filename=file_path.name))
            self._output(self.messages.t('process.target', path=target_path.relative_to(self.config.repo)))
            return ProcessResult(success=True, source_path=file_path, target_path=target_path)
            
        except Exception as e:
            self._output(self.messages.t('process.unknown_error', error=str(e)))
            self._move_to_failed(file_path)
            return ProcessResult(success=False, source_path=file_path, error=str(e))
    
    def _handle_git_failure(self, target_path: Path, original_path: Path, error: GitError):
        try:
            if original_path.parent.exists():
                shutil.move(str(target_path), str(original_path))
                self._output(self.messages.t('process.git_failed_moved_back', error=str(error)))
            else:
                self._move_to_failed(target_path)
                self._output(self.messages.t('process.git_failed', error=str(error)))
        except Exception as e:
            self._output(self.messages.t('process.file_recovery_failed', error=str(e)))
    
    def _move_to_failed(self, file_path: Path):
        try:
            self.config.failed.mkdir(parents=True, exist_ok=True)
            failed_path = self.config.failed / file_path.name
            
            if failed_path.exists():
                failed_path = self.config.failed / f"{file_path.stem}_{datetime.now():%Y%m%d_%H%M%S}{file_path.suffix}"
            
            if file_path.exists():
                shutil.move(str(file_path), str(failed_path))
            self._output(self.messages.t('process.move_to_failed', path=failed_path))
        except Exception as e:
            self._output(self.messages.t('process.move_to_failed_error', error=str(e)))
    
    def process_batch(self, files: list[Path]) -> tuple[int, int]:
        success = failed = 0
        
        for i, file_path in enumerate(files, 1):
            self._output(self.messages.t('process.processing',
                                current=i, total=len(files), filename=file_path.name))
            
            if self.process(file_path).success:
                success += 1
            else:
                failed += 1
        
        return success, failed

"""文件处理器"""

import shutil
from pathlib import Path
from datetime import datetime

from .config import Config
from .git_repo import GitRepo, GitError
from .path_generator import PathGenerator
from ..parsers import FilenameParser, ParseError
from ..exceptions import ProcessError


class FileProcessor:
    """文件处理器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.messages = config.messages
        self.parser = FilenameParser(config.naming_pattern, self.messages)
        self.path_gen = PathGenerator(config.path_template, config.asset_root, self.messages)
        self.repo = GitRepo(config.repo, self.messages)
    
    def process(self, file_path: Path) -> bool:
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
                return False
            
            print(self.messages.t('process.success', filename=file_path.name))
            print(self.messages.t('process.target', path=target_path.relative_to(self.config.repo)))
            return True
            
        except ProcessError as e:
            print(self.messages.t('process.unknown_error', error=str(e)))
            self._move_to_failed(file_path)
            return False
        except Exception as e:
            print(self.messages.t('process.unknown_error', error=str(e)))
            self._move_to_failed(file_path)
            return False
    
    def _handle_git_failure(self, target_path: Path, original_path: Path, error: GitError):
        try:
            if original_path.parent.exists():
                shutil.move(str(target_path), str(original_path))
                print(self.messages.t('process.git_failed_moved_back', error=str(error)))
            else:
                self._move_to_failed(target_path)
                print(self.messages.t('process.git_failed', error=str(error)))
        except Exception as e:
            print(self.messages.t('process.file_recovery_failed', error=str(e)))
    
    def _move_to_failed(self, file_path: Path):
        try:
            self.config.failed.mkdir(parents=True, exist_ok=True)
            failed_path = self.config.failed / file_path.name
            
            if failed_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                stem = file_path.stem
                suffix = file_path.suffix
                failed_path = self.config.failed / f"{stem}_{timestamp}{suffix}"
            
            shutil.move(str(file_path), str(failed_path))
            print(self.messages.t('process.move_to_failed', path=failed_path))
        except Exception as e:
            print(self.messages.t('process.move_to_failed_error', error=str(e)))
    
    def process_batch(self, files: list[Path]) -> tuple[int, int]:
        success = 0
        failed = 0
        
        for i, file_path in enumerate(files, 1):
            print(self.messages.t('process.processing',
                                current=i,
                                total=len(files),
                                filename=file_path.name))
            
            if self.process(file_path):
                success += 1
            else:
                failed += 1
        
        return success, failed

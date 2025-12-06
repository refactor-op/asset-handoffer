"""Git仓库管理"""

import subprocess
from pathlib import Path
from typing import Optional

from ..exceptions import GitError
from ..i18n import Messages


class GitRepo:
    """Git仓库管理"""
    
    def __init__(self, repo_path: Path, messages: Messages = None):
        self.repo_path = repo_path
        self.messages = messages or Messages('zh-CN')
    
    def exists(self) -> bool:
        return (self.repo_path / ".git").exists()
    
    def clone(self, git_url: str, branch: str = "main"):
        if self.exists():
            raise GitError(self.messages.t('git.repo_exists', path=self.repo_path))
        
        try:
            subprocess.run(
                ['git', 'clone', '-b', branch, '--single-branch', git_url, str(self.repo_path)],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            raise GitError(self.messages.t('git.clone_failed', error=e.stderr))
    
    def pull(self):
        try:
            self._run_git(['pull'])
        except subprocess.CalledProcessError as e:
            raise GitError(self.messages.t('git.pull_failed_new', error=e.stderr))
    
    def add(self, file_path: Path):
        try:
            rel_path = file_path.relative_to(self.repo_path)
            self._run_git(['add', str(rel_path)])
        except ValueError:
            raise GitError(self.messages.t('git.file_not_in_repo', path=file_path))
        except subprocess.CalledProcessError as e:
            raise GitError(self.messages.t('git.add_failed', error=e.stderr))
    
    def commit(self, message: str):
        try:
            self._run_git(['commit', '-m', message])
        except subprocess.CalledProcessError as e:
            if "nothing to commit" in e.stderr:
                return
            raise GitError(self.messages.t('git.commit_failed', error=e.stderr))
    
    def push(self, branch: Optional[str] = None):
        try:
            if branch:
                self._run_git(['push', 'origin', branch])
            else:
                self._run_git(['push'])
        except subprocess.CalledProcessError as e:
            raise GitError(self.messages.t('git.push_failed_new', error=e.stderr))
    
    def remove(self, file_path: Path):
        try:
            rel_path = file_path.relative_to(self.repo_path)
            self._run_git(['rm', str(rel_path)])
        except ValueError:
            raise GitError(self.messages.t('git.file_not_in_repo', path=file_path))
        except subprocess.CalledProcessError as e:
            raise GitError(self.messages.t('git.push_failed_new', error=e.stderr))
    
    def _run_git(self, args: list) -> subprocess.CompletedProcess:
        return subprocess.run(
            ['git'] + args,
            cwd=str(self.repo_path),
            check=True,
            capture_output=True,
            text=True
        )

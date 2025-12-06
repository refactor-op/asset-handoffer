"""Git仓库管理"""

import subprocess
import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urlunparse

from ..exceptions import GitError
from ..i18n import Messages


class GitRepo:
    """Git仓库管理"""
    
    def __init__(self, repo_path: Path, messages: Messages = None, token: str = None):
        self.repo_path = repo_path
        self.messages = messages or Messages('zh-CN')
        self.token = token or os.getenv('GITHUB_TOKEN')
    
    def exists(self) -> bool:
        return (self.repo_path / ".git").exists()
    
    def _inject_token(self, git_url: str) -> str:
        """将 token 注入到 Git URL"""
        if not self.token:
            return git_url
        
        parsed = urlparse(git_url)
        if parsed.scheme not in ('https', 'http'):
            return git_url
        
        netloc_with_token = f"{self.token}@{parsed.netloc}"
        return urlunparse((
            parsed.scheme,
            netloc_with_token,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
    
    def clone(self, git_url: str, branch: str = "main"):
        if self.exists():
            raise GitError(self.messages.t('git.repo_exists', path=self.repo_path))
        
        url_with_token = self._inject_token(git_url)
        
        env = os.environ.copy()
        if self.token:
            env['GIT_TERMINAL_PROMPT'] = '0'
            env['GCM_INTERACTIVE'] = 'never'
        
        try:
            subprocess.run(
                ['git', 'clone', '-b', branch, '--single-branch', 
                 '-c', 'credential.helper=', url_with_token, str(self.repo_path)],
                check=True,
                capture_output=True,
                text=True,
                env=env
            )
            
            if self.token:
                subprocess.run(
                    ['git', 'config', 'credential.helper', ''],
                    cwd=str(self.repo_path),
                    check=True,
                    capture_output=True
                )
                
                subprocess.run(
                    ['git', 'remote', 'set-url', 'origin', url_with_token],
                    cwd=str(self.repo_path),
                    check=True,
                    capture_output=True
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

import subprocess
import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urlunparse

from .exceptions import GitError
from .i18n import Messages


class GitRepo:
    def __init__(self, repo_path: Path, messages: Messages = None, token: str = None):
        self.repo_path = repo_path
        self.messages = messages or Messages()
        self.token = token or os.getenv('GIT_TOKEN') or os.getenv('GITHUB_TOKEN')
    
    def exists(self) -> bool:
        return (self.repo_path / ".git").exists()
    
    def verify_remote(self, git_url: str, branch: str = "main") -> bool:
        """验证远程仓库是否可访问（不创建任何本地文件）"""
        url_with_token = self._inject_token(git_url)
        try:
            self._run_git(['ls-remote', '--exit-code', '-h', url_with_token, branch], cwd=None)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def clone(self, git_url: str, branch: str = "main", 
              user_name: str = "Asset Handoffer", 
              user_email: str = "asset-handoffer@local"):
        if self.exists():
            raise GitError(self.messages.t('git.repo_exists', path=self.repo_path))
        
        url_with_token = self._inject_token(git_url)
        
        try:
            self._run_git([
                'clone', '-b', branch, '--single-branch',
                '-c', 'credential.helper=', url_with_token, str(self.repo_path)
            ], cwd=None)
            
            if self.token:
                self._run_git(['config', 'credential.helper', ''])
                self._run_git(['remote', 'set-url', 'origin', url_with_token])
            
            self._run_git(['config', 'user.name', user_name], check=False)
            self._run_git(['config', 'user.email', user_email], check=False)
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
            if "nothing to commit" not in e.stderr:
                raise GitError(self.messages.t('git.commit_failed', error=e.stderr))
    
    def push(self, branch: Optional[str] = None):
        try:
            args = ['push'] + (['origin', branch] if branch else [])
            self._run_git(args)
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
    
    def _inject_token(self, git_url: str) -> str:
        if not self.token:
            return git_url
        
        parsed = urlparse(git_url)
        if parsed.scheme not in ('https', 'http'):
            return git_url
        
        return urlunparse((
            parsed.scheme,
            f"{self.token}@{parsed.netloc}",
            parsed.path, parsed.params, parsed.query, parsed.fragment
        ))
    
    def _get_env(self) -> dict:
        env = os.environ.copy()
        if self.token:
            env['GIT_TERMINAL_PROMPT'] = '0'
            env['GCM_INTERACTIVE'] = 'never'
        return env
    
    def _run_git(self, args: list, cwd: Optional[Path] = ..., check: bool = True) -> subprocess.CompletedProcess:
        """统一的 git 命令执行器"""
        work_dir = str(self.repo_path) if cwd is ... else (str(cwd) if cwd else None)
        return subprocess.run(
            ['git'] + args,
            cwd=work_dir,
            check=check,
            capture_output=True,
            text=True,
            env=self._get_env()
        )


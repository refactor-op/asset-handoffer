import subprocess
import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from .i18n import Messages


class GitError(Exception):
    pass


class GitRepo:
    def __init__(self, repo_path: Path, messages: Messages = None, token: str = None):
        self.repo_path = repo_path
        self.messages = messages or Messages()
        self.token = token or os.getenv("GIT_TOKEN") or os.getenv("GITHUB_TOKEN")

    def exists(self) -> bool:
        return (self.repo_path / ".git").exists()

    def verify_remote(self, git_url: str, branch: str = "main") -> bool:
        url = self._inject_token(git_url)
        try:
            self._run(["ls-remote", "--exit-code", "-h", url, branch], cwd=None)
            return True
        except subprocess.CalledProcessError:
            return False

    def clone(
        self,
        git_url: str,
        branch: str = "main",
        user_name: str = "Asset Handoffer",
        user_email: str = "asset-handoffer@local",
    ):
        if self.exists():
            raise GitError(self.messages.t("git.repo_exists", path=self.repo_path))

        url = self._inject_token(git_url)

        try:
            self._run(
                [
                    "clone",
                    "-b",
                    branch,
                    "--single-branch",
                    "-c",
                    "credential.helper=",
                    url,
                    str(self.repo_path),
                ],
                cwd=None,
            )

            if self.token:
                self._run(["config", "credential.helper", ""])
                self._run(["remote", "set-url", "origin", url])

            self._run(["config", "user.name", user_name], check=False)
            self._run(["config", "user.email", user_email], check=False)
        except subprocess.CalledProcessError as e:
            raise GitError(self.messages.t("git.clone_failed", error=e.stderr))

    def pull(self):
        try:
            self._run(["pull"])
        except subprocess.CalledProcessError as e:
            raise GitError(self.messages.t("git.pull_failed_new", error=e.stderr))

    def add(self, file_path: Path):
        try:
            rel_path = file_path.relative_to(self.repo_path)
            self._run(["add", str(rel_path)])
        except ValueError:
            raise GitError(self.messages.t("git.file_not_in_repo", path=file_path))
        except subprocess.CalledProcessError as e:
            raise GitError(self.messages.t("git.add_failed", error=e.stderr))

    def commit(self, message: str):
        try:
            self._run(["commit", "-m", message])
        except subprocess.CalledProcessError as e:
            if "nothing to commit" not in e.stderr:
                raise GitError(self.messages.t("git.commit_failed", error=e.stderr))

    def push(self, branch: str = None):
        try:
            args = ["push"] + (["origin", branch] if branch else [])
            self._run(args)
        except subprocess.CalledProcessError as e:
            raise GitError(self.messages.t("git.push_failed_new", error=e.stderr))

    def remove(self, file_path: Path):
        try:
            rel_path = file_path.relative_to(self.repo_path)
            self._run(["rm", str(rel_path)])
        except ValueError:
            raise GitError(self.messages.t("git.file_not_in_repo", path=file_path))
        except subprocess.CalledProcessError as e:
            raise GitError(self.messages.t("git.remove_failed", error=e.stderr))

    def _inject_token(self, git_url: str) -> str:
        if not self.token:
            return git_url
        parsed = urlparse(git_url)
        if parsed.scheme not in ("https", "http"):
            return git_url
        return urlunparse(
            (
                parsed.scheme,
                f"{self.token}@{parsed.netloc}",
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            )
        )

    def _run(
        self, args: list, cwd: Path | None = ..., check: bool = True
    ) -> subprocess.CompletedProcess:
        work_dir = str(self.repo_path) if cwd is ... else (str(cwd) if cwd else None)
        env = os.environ.copy()
        if self.token:
            env["GIT_TERMINAL_PROMPT"] = "0"
            env["GCM_INTERACTIVE"] = "never"
        return subprocess.run(
            ["git"] + args,
            cwd=work_dir,
            check=check,
            capture_output=True,
            text=True,
            env=env,
        )

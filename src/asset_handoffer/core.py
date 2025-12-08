import re
import shutil
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Callable, NamedTuple
import yaml

from .i18n import Messages


class ConfigError(Exception):
    pass


class ParseError(Exception):
    pass


class ProcessError(Exception):
    pass


class ProcessResult(NamedTuple):
    success: bool
    message: str
    target_path: Path | None = None


@dataclass
class Config:
    data: dict
    config_file: Path
    messages: Messages
    workspace_root: Path
    inbox: Path
    repo: Path
    failed: Path

    @staticmethod
    def load(config_file: Path) -> "Config":
        m = Messages()

        if not config_file.exists():
            raise ConfigError(m.t("config.file_not_found", path=str(config_file)))

        try:
            data = yaml.safe_load(config_file.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            raise ConfigError(m.t("config.invalid_yaml", error=str(e)))

        m = Messages(data.get("language"))

        workspace = data.get("workspace", "./")
        if isinstance(workspace, dict):
            root = workspace.get("root", "./")
            inbox_name = workspace.get("inbox", "inbox")
            repo_name = workspace.get("repo", ".repo")
            failed_name = workspace.get("failed", "failed")
        else:
            root, inbox_name, repo_name, failed_name = workspace, "inbox", ".repo", "failed"

        root_path = Path(root)
        if not root_path.is_absolute():
            root_path = (config_file.parent / root).resolve()

        config = Config(
            data=data,
            config_file=config_file,
            messages=m,
            workspace_root=root_path,
            inbox=root_path / inbox_name,
            repo=root_path / repo_name,
            failed=root_path / failed_name,
        )
        config._validate()
        return config

    def _validate(self):
        m = self.messages
        has_rules = self.data.get("naming", {}).get("rules")
        has_pattern = self.data.get("naming", {}).get("pattern")

        if not has_rules and not has_pattern:
            raise ConfigError(m.t("config.missing_field", field="naming.rules or naming.pattern"))
        if not self.data.get("git", {}).get("repository"):
            raise ConfigError(m.t("config.missing_field", field="git.repository"))
        if "asset_root" not in self.data:
            raise ConfigError(m.t("config.missing_field", field="asset_root"))
        if not has_rules and "path_template" not in self.data:
            raise ConfigError(m.t("config.missing_field", field="path_template"))

    @property
    def git_url(self) -> str:
        return self.data["git"]["repository"]

    @property
    def git_branch(self) -> str:
        return self.data.get("git", {}).get("branch", "main")

    @property
    def git_token(self) -> str:
        return self.data.get("git", {}).get("token", "")

    @property
    def git_commit_template(self) -> str:
        return self.data.get("git", {}).get("commit_message", "Update: {name}")

    @property
    def git_user_name(self) -> str:
        return self.data.get("git", {}).get("user", {}).get("name", "Asset Handoffer")

    @property
    def git_user_email(self) -> str:
        return self.data.get("git", {}).get("user", {}).get("email", "asset-handoffer@local")

    @property
    def asset_root(self) -> str:
        return self.data.get("asset_root", "")

    @property
    def path_template(self) -> str:
        return self.data.get("path_template", "")

    @property
    def naming_rules(self) -> list[dict]:
        rules = self.data.get("naming", {}).get("rules")
        if rules:
            return rules
        pattern = self.data.get("naming", {}).get("pattern")
        if pattern:
            return [{
                "pattern": pattern,
                "path_template": self.path_template,
                "example": self.data.get("naming", {}).get("example", ""),
            }]
        return []

    @property
    def naming_examples(self) -> list[str]:
        return [r.get("example", "") for r in self.naming_rules if r.get("example")]

    def ensure_dirs(self):
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.failed.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def create(git_url: str, asset_root: str = "Assets/GameRes/",
               output_file: Path = None) -> Path:
        template_path = Path(__file__).parent / "templates" / "config.yaml"

        if not template_path.exists():
            raise ConfigError(f"Template not found: {template_path}")

        content = template_path.read_text(encoding="utf-8")
        content = content.replace('asset_root: "Assets/GameRes/"', f'asset_root: "{asset_root}"')
        content = content.replace(
            'repository: "https://your-git-host.com/your-org/your-project.git"',
            f'repository: "{git_url}"'
        )

        if output_file is None:
            project_name = git_url.rstrip("/").split("/")[-1].replace(".git", "")
            output_file = Path(f"{project_name}.yaml")

        output_file.write_text(content, encoding="utf-8")
        return output_file


def parse_filename(filename: str, rules: list[dict]) -> dict | None:
    for rule in rules:
        pattern = rule.get("pattern", "")
        try:
            compiled = re.compile(pattern)
        except re.error:
            continue

        match = compiled.match(filename)
        if match:
            groups = match.groupdict()
            if "ext" not in groups and "extension" not in groups:
                continue
            return {
                "groups": groups,
                "path_template": rule.get("path_template", ""),
                "original_name": filename,
            }
    return None


def compute_target_path(parsed: dict, default_template: str,
                        asset_root: str, repo_base: Path) -> Path:
    template = parsed.get("path_template") or default_template
    groups = parsed["groups"]

    try:
        rel_path = template.format(**groups)
    except KeyError as e:
        raise ProcessError(f"Template uses undefined field: {e}")

    return repo_base / asset_root / rel_path


def process_file(file_path: Path, config: Config,
                 output: Callable[[str], None] = print) -> ProcessResult:
    from .git import GitRepo, GitError

    m = config.messages
    repo = GitRepo(config.repo, m, config.git_token)

    if not repo.exists():
        return ProcessResult(False, m.t("process.repo_not_exists"))

    parsed = parse_filename(file_path.name, config.naming_rules)
    if not parsed:
        msg = m.t("process.filename_error",
                  error=m.t("parse.filename_not_match", filename=file_path.name),
                  example=", ".join(config.naming_examples))
        _move_to_failed(file_path, config)
        return ProcessResult(False, msg)

    try:
        target_path = compute_target_path(parsed, config.path_template,
                                          config.asset_root, config.repo)
    except ProcessError as e:
        _move_to_failed(file_path, config)
        return ProcessResult(False, str(e))

    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(file_path), str(target_path))

    try:
        repo.add(target_path)
        commit_msg = config.git_commit_template.format(**parsed["groups"])
        repo.commit(commit_msg)
        repo.push()
    except GitError as e:
        if file_path.parent.exists():
            shutil.move(str(target_path), str(file_path))
            return ProcessResult(False, m.t("process.git_failed_moved_back", error=str(e)))
        else:
            _move_to_failed(target_path, config)
            return ProcessResult(False, m.t("process.git_failed", error=str(e)))

    output(m.t("process.success", filename=file_path.name))
    output(m.t("process.target", path=target_path.relative_to(config.repo)))
    return ProcessResult(True, str(target_path), target_path)


def _move_to_failed(file_path: Path, config: Config):
    config.failed.mkdir(parents=True, exist_ok=True)
    failed_path = config.failed / file_path.name
    if failed_path.exists():
        stem = file_path.stem
        suffix = file_path.suffix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        failed_path = config.failed / f"{stem}_{timestamp}{suffix}"
    if file_path.exists():
        shutil.move(str(file_path), str(failed_path))


def process_batch(files: list[Path], config: Config,
                  output: Callable[[str], None] = print) -> tuple[int, int]:
    m = config.messages
    success = failed = 0

    for i, file_path in enumerate(files, 1):
        output(m.t("process.processing", current=i, total=len(files), filename=file_path.name))
        result = process_file(file_path, config, output)
        if result.success:
            success += 1
        else:
            failed += 1

    return success, failed

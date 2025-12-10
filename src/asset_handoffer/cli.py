import typer
from pathlib import Path
import shutil

from .core import (
    Config,
    ConfigError,
    ProcessError,
    parse_filename,
    compute_target_path,
    process_file,
    process_batch,
)
from .git import GitRepo, GitError
from .i18n import Messages

app = typer.Typer(help="资产交付器", no_args_is_help=True)


def load_config(config_file: Path) -> Config:
    try:
        return Config.load(config_file)
    except ConfigError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1)


@app.command()
def init(
    git_url: str = typer.Option(..., prompt="Git仓库URL"),
    asset_root: str = typer.Option("Assets/GameRes/", prompt="资产根路径"),
    branch: str = typer.Option("main", prompt="分支名"),
    token: str = typer.Option("", prompt="Git Token (可选，直接回车跳过)"),
    user_name: str = typer.Option("", prompt="提交用户名 (可选，直接回车跳过)"),
    user_email: str = typer.Option("", prompt="提交邮箱 (可选，直接回车跳过)"),
    output: Path = typer.Option(None, "-o", "--output"),
):
    """生成配置文件"""
    m = Messages()
    try:
        config_file = Config.create(
            git_url=git_url,
            asset_root=asset_root,
            output_file=output,
            branch=branch,
            token=token,
            user_name=user_name,
            user_email=user_email,
        )
        typer.echo(m.t("init.created", path=config_file))
        typer.echo(m.t("init.next_steps"))
        typer.echo(m.t("init.next_setup", config=config_file))
    except Exception as e:
        typer.echo(m.t("init.failed", error=str(e)), err=True)
        raise typer.Exit(1)


@app.command()
def setup(
    config_file: Path,
    yes: bool = typer.Option(False, "-y", "--yes", help="跳过确认"),
):
    """初始化工作区"""
    config = load_config(config_file)
    m = config.messages
    repo = GitRepo(config.repo, m, config.git_token)

    typer.echo(m.t("setup.repository", url=config.git_url))
    typer.echo(m.t("setup.workspace", path=config.workspace_root))

    if repo.exists():
        typer.echo(m.t("setup.repo_exists_warning", path=config.repo))
        if not (yes or typer.confirm(m.t("setup.repo_exists_confirm"))):
            typer.echo(m.t("setup.skip_clone"))
            return
        shutil.rmtree(config.repo)

    typer.echo(m.t("setup.verifying"))
    if not repo.verify_remote(config.git_url, config.git_branch):
        typer.echo(m.t("git.verify_failed"), err=True)
        raise typer.Exit(1)

    config.ensure_dirs()
    typer.echo(m.t("setup.cloning"))

    try:
        repo.clone(
            config.git_url,
            config.git_branch,
            config.git_user_name,
            config.git_user_email,
        )
    except GitError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1)

    typer.echo(m.t("setup.done_title"))
    typer.echo(m.t("setup.usage_put_files", inbox=config.inbox))
    typer.echo(m.t("setup.usage_run_handoff"))


@app.command()
def process(
    config_file: Path,
    files: list[Path] = typer.Option(None, "-f", "--file"),
    yes: bool = typer.Option(False, "-y", "--yes", help="跳过确认"),
):
    """处理并提交文件"""
    config = load_config(config_file)
    m = config.messages
    repo = GitRepo(config.repo, m, config.git_token)

    if not repo.exists():
        typer.echo(m.t("process.repo_not_exists"), err=True)
        raise typer.Exit(1)

    file_list = files or [f for f in config.inbox.iterdir() if f.is_file()]
    if not file_list:
        typer.echo(m.t("status.empty"))
        return

    typer.echo(m.t("process.syncing"))
    try:
        repo.pull()
    except GitError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1)

    valid = []
    invalid = []
    overrides = []

    for f in file_list:
        parsed = parse_filename(f.name, config.naming_rules)
        if not parsed:
            invalid.append(f)
            continue
        try:
            target = compute_target_path(
                parsed, config.path_template, config.asset_root, config.repo
            )
        except ProcessError:
            invalid.append(f)
            continue
        is_override = target.exists()
        valid.append((f, target, is_override))
        if is_override:
            overrides.append(f)

    typer.echo(m.t("process.found_files", count=len(file_list)))
    typer.echo()

    for f, target, is_override in valid:
        suffix = m.t("process.status_override") if is_override else ""
        typer.echo(f"  {f.name} -> {target.relative_to(config.repo)} {suffix}".rstrip())

    for f in invalid:
        typer.echo(f"  {f.name} -> {m.t('process.status_invalid')}")

    if not valid:
        typer.echo(m.t("process.no_valid_files"))
        return

    if not yes:
        typer.echo()
        prompt = (
            m.t("process.override_confirm", count=len(overrides))
            if overrides
            else m.t("process.confirm")
        )
        if not typer.confirm(prompt):
            typer.echo(m.t("delete.cancelled"))
            return

    typer.echo()
    success_count = 0
    failed_count = len(invalid)

    for i, (f, target, _) in enumerate(valid, 1):
        typer.echo(
            m.t("process.processing", current=i, total=len(valid), filename=f.name)
        )
        result = process_file(f, config, output=typer.echo)
        if result.success:
            success_count += 1
        else:
            failed_count += 1

    # 统一 push 所有 commits
    if success_count > 0:
        typer.echo()
        typer.echo(m.t("process.pushing"))
        try:
            repo.push()
        except GitError as e:
            typer.echo(m.t("process.push_failed", error=str(e)), err=True)
            raise typer.Exit(1)

    typer.echo()
    typer.echo(m.t("process.summary_success", success=success_count))
    typer.echo(m.t("process.summary_failed", failed=failed_count))

    if failed_count > 0:
        typer.echo(m.t("process.failed_files_hint", path=config.failed))
        raise typer.Exit(1)


@app.command()
def status(config_file: Path):
    """查看收件箱状态"""
    config = load_config(config_file)
    m = config.messages

    files = [f for f in config.inbox.iterdir() if f.is_file()]
    typer.echo(m.t("setup.inbox_dir", path=config.inbox))
    typer.echo()

    if not files:
        typer.echo(m.t("status.empty"))
        return

    typer.echo(m.t("status.count", count=len(files)))
    typer.echo()

    for f in files:
        size_mb = f.stat().st_size / (1024 * 1024)
        parsed = parse_filename(f.name, config.naming_rules)
        if parsed:
            try:
                target = compute_target_path(
                    parsed, config.path_template, config.asset_root, config.repo
                )
                typer.echo(
                    f"  {f.name} ({size_mb:.1f}MB) -> {target.relative_to(config.repo)}"
                )
            except ProcessError:
                typer.echo(
                    f"  {f.name} ({size_mb:.1f}MB) -> {m.t('process.status_invalid')}"
                )
        else:
            typer.echo(
                f"  {f.name} ({size_mb:.1f}MB) -> {m.t('process.status_invalid')}"
            )


@app.command()
def delete(
    pattern: str,
    config_file: Path,
    yes: bool = typer.Option(False, "-y", "--yes"),
):
    """删除仓库中的文件"""
    config = load_config(config_file)
    m = config.messages
    repo = GitRepo(config.repo, m, config.git_token)

    matches = list(config.repo.rglob(pattern))
    if not matches:
        typer.echo(m.t("delete.not_found", pattern=pattern))
        return

    typer.echo(m.t("delete.found", count=len(matches)))
    for match in matches:
        typer.echo(f"  {match.relative_to(config.repo)}")

    if not (yes or typer.confirm(m.t("delete.confirm"))):
        typer.echo(m.t("delete.cancelled"))
        return

    for match in matches:
        match.unlink()
        repo.remove(match)

    repo.commit(f"Delete: {pattern}")
    repo.push()
    typer.echo(m.t("delete.deleted", count=len(matches)))


def main():
    app()


if __name__ == "__main__":
    main()

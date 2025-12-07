import typer
from pathlib import Path
from .core import Config, ConfigError, GitRepo, GitError, FileProcessor, Messages

app = typer.Typer(help="资产交付器", no_args_is_help=True)

SEPARATOR = "=" * 60


@app.command()
def init(
    git_url: str = typer.Option(..., prompt="Git仓库URL"),
    asset_root: str = typer.Option("Assets/GameRes/", prompt="Unity资产根路径"),
    output: Path = typer.Option(None, "--output", "-o", help="输出文件路径")
):
    """创建配置文件"""
    m = Messages()
    try:
        config_file = Config.create(git_url=git_url, asset_root=asset_root, output_file=output)
        print(m.t('init.created', path=config_file))
        print(m.t('init.next_steps'))
        print(m.t('init.next_git_credential'))
        print(m.t('init.next_distribute'))
        print(m.t('init.next_setup', config=config_file))
    except Exception as e:
        print(m.t('init.failed', error=str(e)))
        raise typer.Exit(1)


@app.command()
def setup(config_file: Path):
    """设置工作区（首次使用）"""
    try:
        config = Config.load(config_file)
        m = config.messages
        
        print(SEPARATOR)
        print(f"  {m.t('setup.title')}")
        print(SEPARATOR)
        print(m.t('setup.repository', url=config.git_url))
        print(m.t('setup.workspace', path=config.workspace_root))
        print()
        
        repo = GitRepo(config.repo, m, config.git_token)
        
        should_clone = True
        if repo.exists():
            print(m.t('setup.repo_exists_warning', path=config.repo))
            if typer.confirm(m.t('setup.repo_exists_confirm')):
                import shutil
                shutil.rmtree(config.repo)
            else:
                print(m.t('setup.skip_clone'))
                should_clone = False
        
        if should_clone:
            print(m.t('setup.verifying'))
            if not repo.verify_remote(config.git_url, config.git_branch):
                print(m.t('git.verify_failed'))
                raise typer.Exit(1)
            
            config.ensure_dirs()
            print(m.t('setup.inbox_dir', path=config.inbox))
            print()
            print(m.t('setup.cloning'))
            try:
                repo.clone(config.git_url, config.git_branch,
                          user_name=config.git_user_name, user_email=config.git_user_email)
                print(m.t('setup.cloned', path=config.repo))
            except GitError as e:
                print(str(e))
                raise typer.Exit(1)
        else:
            config.ensure_dirs()
            print(m.t('setup.inbox_dir', path=config.inbox))
        
        print()
        print(SEPARATOR)
        print(f"  {m.t('setup.done_title')}")
        print(SEPARATOR)
        print()
        print(m.t('setup.usage_hint'))
        print(m.t('setup.usage_put_files', inbox=config.inbox))
        print(m.t('setup.usage_run_process', config=config_file))
        print()
        
    except ConfigError as e:
        print(str(e))
        raise typer.Exit(1)


@app.command()
def process(
    config_file: Path = typer.Argument(..., help="配置文件路径"),
    files: list[Path] = typer.Option(None, "--file", "-f", help="指定文件")
):
    """处理并提交文件"""
    try:
        config = Config.load(config_file)
        m = config.messages
        
        file_list = files if files else [f for f in config.inbox.iterdir() if f.is_file()]
        
        if not file_list:
            print(m.t('status.empty'))
            print(m.t('setup.inbox_dir', path=config.inbox))
            return
        
        print(m.t('process.found_files', count=len(file_list)))
        print()
        
        processor = FileProcessor(config)
        success, failed = processor.process_batch(file_list)
        
        print()
        print(SEPARATOR)
        print(f"  {m.t('process.result_all_success') if failed == 0 else m.t('process.result_partial_failure')}")
        print(SEPARATOR)
        print()
        print(m.t('process.summary_success', success=success))
        print(m.t('process.summary_failed', failed=failed))
        
        if failed > 0:
            print()
            print(m.t('process.failed_files_hint', path=config.failed))
            raise typer.Exit(1)
        
    except ConfigError as e:
        print(str(e))
        raise typer.Exit(1)


@app.command()
def delete(
    pattern: str = typer.Argument(..., help="文件名模式"),
    config_file: Path = typer.Argument(..., help="配置文件路径")
):
    """删除仓库中的文件"""
    try:
        config = Config.load(config_file)
        m = config.messages
        repo = GitRepo(config.repo, m, config.git_token)
        
        matches = list(config.repo.rglob(pattern))
        
        if not matches:
            print(m.t('delete.not_found', pattern=pattern))
            return
        
        print(m.t('delete.found', count=len(matches)))
        print()
        for match in matches:
            print(m.t('delete.file_item', path=match.relative_to(config.repo)))
        
        if not typer.confirm(f"\n{m.t('delete.confirm')}"):
            print(m.t('delete.cancelled'))
            return
        
        for match in matches:
            match.unlink()
            repo.remove(match)
        
        repo.commit(f"Delete: {pattern}")
        repo.push()
        
        print()
        print(m.t('delete.deleted', count=len(matches)))
        
    except Exception as e:
        print(Messages().t('delete.failed', error=str(e)))
        raise typer.Exit(1)


@app.command()
def status(config_file: Path = typer.Argument(..., help="配置文件路径")):
    """查看收件箱状态"""
    try:
        config = Config.load(config_file)
        m = config.messages
        
        files = [f for f in config.inbox.iterdir() if f.is_file()]
        
        print(m.t('setup.inbox_dir', path=config.inbox))
        print()
        
        if not files:
            print(m.t('status.empty'))
            return
        
        print(m.t('status.count', count=len(files)))
        print()
        
        MB = 1024 * 1024
        for f in files:
            print(m.t('status.file_item', name=f.name, size=f.stat().st_size / MB))
        
        print()
        print(m.t('status.run_hint', config=config_file))
        
    except Exception as e:
        print(f"Error: {e}")
        raise typer.Exit(1)


def main():
    app()


if __name__ == "__main__":
    main()

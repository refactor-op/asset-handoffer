"""CLI命令行界面"""

import typer
from pathlib import Path

from .core.config import Config, ConfigError
from .core.git_repo import GitRepo, GitError
from .core.processor import FileProcessor

from .i18n import get_messages

app = typer.Typer(
    help="Asset Handoffer - 资产交接自动化工具",
    no_args_is_help=True
)


@app.command()
def init(
    git_url: str = typer.Option(..., prompt="GitHub仓库URL"),
    asset_root: str = typer.Option("Assets/GameRes/", prompt="Unity资产根路径"),
    output: Path = typer.Option(None, "--output", "-o", help="输出文件路径")
):
    """创建配置文件（程序员使用）
    
    生成一个配置文件，包含项目的所有必要信息。
    将此配置文件发给美术人员使用。
    """
    m = get_messages('zh-CN')
    
    try:
        config_file = Config.create(
            git_url=git_url,
            asset_root=asset_root,
            output_file=output
        )
        
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
    """设置工作区（美术使用）
    
    首次使用时运行此命令，将：
    1. 创建工作区目录（inbox等）
    2. 克隆Git仓库到本地
    """
    try:
        config = Config.load(config_file)
        m = config.messages
        
        print("=" * 60)
        print(f"  {m.t('setup.title')}")
        print("=" * 60)
        print(m.t('setup.repository', url=config.git_url))
        print(m.t('setup.workspace', path=config.workspace_root))
        print()
        
        config.ensure_dirs()
        print(m.t('setup.inbox_dir', path=config.inbox))
        
        repo = GitRepo(config.repo, m, config.git_token)
        
        if repo.exists():
            print(m.t('setup.repo_exists_warning', path=config.repo))
            if not typer.confirm(m.t('setup.repo_exists_confirm')):
                print(m.t('setup.skip_clone'))
            else:
                import shutil
                shutil.rmtree(config.repo)
                repo_exists = False
        else:
            repo_exists = False
        
        if not repo_exists or not repo.exists():
            print()
            print(m.t('setup.cloning'))
            try:
                repo.clone(config.git_url, config.git_branch, 
                          user_name=config.git_user_name,
                          user_email=config.git_user_email)
                print(m.t('setup.cloned', path=config.repo))
            except GitError as e:
                print(str(e))
                raise typer.Exit(1)
        
        print()
        print("=" * 60)
        print(f"  {m.t('setup.done_title')}")
        print("=" * 60)
        print()
        print(m.t('setup.usage_hint'))
        print(m.t('setup.usage_put_files', inbox=config.inbox))
        print(m.t('setup.usage_run_process', config=config_file))
        print()
        
    except ConfigError as e:
        print(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print(f"Error: {e}")
        raise typer.Exit(1)


@app.command()
def process(
    config_file: Path = typer.Argument(..., help="配置文件路径"),
    files: list[Path] = typer.Option(None, "--file", "-f", help="指定文件（可多次）")
):
    """处理文件（提交到GitHub）
    
    从inbox读取文件，移动到正确位置，并提交到GitHub。
    """
    try:
        config = Config.load(config_file)
        m = config.messages
        
        processor = FileProcessor(config)
        
        if files:
            file_list = files
        else:
            file_list = [f for f in config.inbox.iterdir() if f.is_file()]
        
        if not file_list:
            print(m.t('status.empty'))
            print(m.t('setup.inbox_dir', path=config.inbox))
            return
        
        print(m.t('process.found_files', count=len(file_list)))
        print()
        
        success, failed = processor.process_batch(file_list)
        
        print()
        print("=" * 60)
        if failed == 0:
            print(f"  {m.t('process.result_all_success')}")
        else:
            print(f"  {m.t('process.result_partial_failure')}")
        print("=" * 60)
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
    except Exception as e:
        print(f"Error: {e}")
        raise typer.Exit(1)


@app.command()
def delete(
    pattern: str = typer.Argument(..., help="文件名模式（支持通配符）"),
    config_file: Path = typer.Argument(..., help="配置文件路径")
):
    """删除文件（从本地仓库删除并push）
    
    示例：
        asset-handoffer delete "Hero_*.fbx" config.yaml
    """
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
            rel_path = match.relative_to(config.repo)
            print(m.t('delete.file_item', path=rel_path))
        
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
        m = get_messages('zh-CN')
        print(m.t('delete.failed', error=str(e)))
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
        for f in files:
            size_mb = f.stat().st_size / (1024 * 1024)
            print(m.t('status.file_item', name=f.name, size=size_mb))
        
        print()
        print(m.t('status.run_hint', config=config_file))
        
    except Exception as e:
        print(f"Error: {e}")
        raise typer.Exit(1)


def main():
    """主入口"""
    app()


if __name__ == "__main__":
    main()

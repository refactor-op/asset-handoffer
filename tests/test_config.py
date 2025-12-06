"""配置管理测试"""

import pytest
from pathlib import Path
from asset_handoffer.core.config import Config


def test_create_and_load_config(tmp_path):
    """测试配置创建和加载"""
    config_file = tmp_path / "test_config.yaml"
    
    Config.create(
        git_url="https://github.com/test/test.git",
        output_file=config_file
    )
    
    assert config_file.exists()
    
    config = Config.load(config_file)
    assert config.git_url == "https://github.com/test/test.git"
    assert config.workspace_root.resolve() == tmp_path.resolve()


def test_workspace_string_shorthand(tmp_path):
    """测试workspace字符串简写"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
workspace: "./"
git:
  repository: "https://github.com/test/test.git"
asset_root: "Assets/"
path_template: "{type}/{name}/"
naming:
  pattern: "^(?P<type>[^_]+)_(?P<name>[^_]+)\\.(?P<ext>\\\\w+)$"
language: "zh-CN"
""")
    
    config = Config.load(config_file)
    assert config.inbox == tmp_path / "inbox"
    assert config.repo == tmp_path / ".repo"

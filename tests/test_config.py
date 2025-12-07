from pathlib import Path
from asset_handoffer.core import Config


def test_create_and_load_config(tmp_path):
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
    config_file = tmp_path / "config.yaml"
    
    yaml_content = '''workspace: "./"
git:
  repository: "https://github.com/test/test.git"
asset_root: "Assets/"
path_template: "{type}/{name}/"
naming:
  pattern: "^(?P<type>[^_]+)_(?P<name>[^_]+)\\\\.(?P<ext>\\\\w+)$"
language: "zh-CN"
'''
    config_file.write_text(yaml_content)
    
    config = Config.load(config_file)
    assert config.inbox == tmp_path / "inbox"
    assert config.repo == tmp_path / ".repo"

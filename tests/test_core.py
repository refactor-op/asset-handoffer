from pathlib import Path

import pytest

from asset_handoffer import Config, parse_filename


def test_config_create_and_load(tmp_path):
    config_file = tmp_path / "test.yaml"
    Config.create(git_url="https://github.com/test/test.git", output_file=config_file)

    assert config_file.exists()

    config = Config.load(config_file)
    assert config.git_url == "https://github.com/test/test.git"


def test_parse_filename_match():
    rules = [
        {
            "pattern": r"^(?P<type>[^_]+)_(?P<name>[^_]+)\.(?P<ext>\w+)$",
            "path_template": "{type}/{name}.{ext}",
        }
    ]
    result = parse_filename("Character_Hero.fbx", rules)
    assert result is not None
    assert result["groups"]["type"] == "Character"
    assert result["groups"]["name"] == "Hero"


def test_parse_filename_no_match():
    rules = [
        {
            "pattern": r"^(?P<type>[^_]+)_(?P<name>[^_]+)\.(?P<ext>\w+)$",
            "path_template": "{type}/{name}.{ext}",
        }
    ]
    result = parse_filename("InvalidName.fbx", rules)
    assert result is None

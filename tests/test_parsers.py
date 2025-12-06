"""文件名解析器测试"""

import pytest
from asset_handoffer.parsers import FilenameParser, ParseError


class TestFilenameParser:
    """测试 FilenameParser 类"""
    
    @pytest.fixture
    def parser(self):
        pattern = r"^(?P<module>[^_]+)_(?P<category>[^_]+)_(?P<feature>[^_]+)(_(?P<variant>[^_]+))?\.(?P<ext>\w+)$"
        return FilenameParser(pattern)

    @pytest.mark.parametrize("filename,expected_module,expected_category,expected_feature", [
        ("GameCore_Character_Hero_Idle.fbx", "GameCore", "Character", "Hero"),
        ("Activity_UiEffect_LevelUp.png", "Activity", "UiEffect", "LevelUp"),
        ("Shop_UiIcon_Coin.jpg", "Shop", "UiIcon", "Coin"),
    ])
    def test_parse_valid_filename(self, parser, filename, expected_module, expected_category, expected_feature):
        """测试解析有效的文件名"""
        result = parser.parse(filename)
        assert result['module'] == expected_module
        assert result['category'] == expected_category
        assert result['feature'] == expected_feature

    @pytest.mark.parametrize("filename", [
        "Invalid.fbx",
        "Game_Core.fbx",
        "NoExtension",
    ])
    def test_parse_invalid_filename(self, parser, filename):
        """测试解析无效的文件名"""
        with pytest.raises(ParseError):
            parser.parse(filename)
    
    def test_dynamic_fields(self):
        """测试动态字段支持"""
        pattern = r"^(?P<type>[^_]+)_(?P<name>[^_]+)\.(?P<ext>\w+)$"
        parser = FilenameParser(pattern)
        
        result = parser.parse("Character_Hero.fbx")
        assert result['type'] == "Character"
        assert result['name'] == "Hero"
        assert result.extension == "fbx"

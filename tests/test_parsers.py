import pytest
from asset_handoffer.core import FilenameParser, ParseError


@pytest.fixture
def single_rule_parser():
    pattern = r"^(?P<module>[^_]+)_(?P<category>[^_]+)_(?P<feature>[^_]+)(_(?P<variant>[^_]+))?\.(?P<ext>\w+)$"
    return FilenameParser(pattern=pattern)


@pytest.fixture
def multi_rule_parser():
    rules = [
        {
            'pattern': r"^(?P<category>[^_]+)_(?P<type>[^_]+)_(?P<name>[^_]+)_(?P<variant>[^_]+)\.(?P<ext>\w+)$",
            'path_template': "{category}/{type}/{name}_{variant}.{ext}",
            'example': "Character_Monster_Clicker_Idle.fbx"
        },
        {
            'pattern': r"^(?P<category>[^_]+)_(?P<type>[^_]+)_(?P<name>[^_]+)\.(?P<ext>\w+)$",
            'path_template': "{category}/{type}/{name}.{ext}",
            'example': "Prop_Tool_Scanner.fbx"
        },
        {
            'pattern': r"^(?P<category>[^_]+)_(?P<name>[^_]+)\.(?P<ext>\w+)$",
            'path_template': "{category}/{name}.{ext}",
            'example': "Audio_Ambient.wav"
        }
    ]
    return FilenameParser(rules=rules)


@pytest.mark.parametrize("filename,expected", [
    ("GameCore_Character_Hero_Idle.fbx", {"module": "GameCore", "category": "Character", "feature": "Hero"}),
    ("Activity_UiEffect_LevelUp.png", {"module": "Activity", "category": "UiEffect", "feature": "LevelUp"}),
])
def test_single_rule_parse(single_rule_parser, filename, expected):
    result = single_rule_parser.parse(filename)
    assert result.groups["module"] == expected["module"]
    assert result.groups["category"] == expected["category"]
    assert result.groups["feature"] == expected["feature"]


def test_multi_rule_four_layer(multi_rule_parser):
    result = multi_rule_parser.parse("Character_Monster_Clicker_Idle.fbx")
    assert result.groups["category"] == "Character"
    assert result.groups["type"] == "Monster"
    assert result.groups["name"] == "Clicker"
    assert result.groups["variant"] == "Idle"
    assert result.path_template == "{category}/{type}/{name}_{variant}.{ext}"


def test_multi_rule_three_layer(multi_rule_parser):
    result = multi_rule_parser.parse("Prop_Tool_Scanner.fbx")
    assert result.groups["category"] == "Prop"
    assert result.groups["type"] == "Tool"
    assert result.groups["name"] == "Scanner"
    assert result.path_template == "{category}/{type}/{name}.{ext}"


def test_multi_rule_two_layer(multi_rule_parser):
    result = multi_rule_parser.parse("Audio_Ambient.wav")
    assert result.groups["category"] == "Audio"
    assert result.groups["name"] == "Ambient"
    assert result.path_template == "{category}/{name}.{ext}"


def test_no_match_raises_error(multi_rule_parser):
    with pytest.raises(ParseError):
        multi_rule_parser.parse("Invalid.fbx")

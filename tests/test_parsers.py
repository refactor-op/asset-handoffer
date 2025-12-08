import pytest
from asset_handoffer import parse_filename, ParseError


@pytest.fixture
def single_rule():
    pattern = r"^(?P<module>[^_]+)_(?P<category>[^_]+)_(?P<feature>[^_]+)(_(?P<variant>[^_]+))?\.(?P<ext>\w+)$"
    return [{"pattern": pattern, "path_template": "", "example": ""}]


@pytest.fixture
def multi_rules():
    return [
        {
            "pattern": r"^(?P<category>[^_]+)_(?P<type>[^_]+)_(?P<name>[^_]+)_(?P<variant>[^_]+)\.(?P<ext>\w+)$",
            "path_template": "{category}/{type}/{name}_{variant}.{ext}",
            "example": "Character_Monster_Clicker_Idle.fbx"
        },
        {
            "pattern": r"^(?P<category>[^_]+)_(?P<type>[^_]+)_(?P<name>[^_]+)\.(?P<ext>\w+)$",
            "path_template": "{category}/{type}/{name}.{ext}",
            "example": "Prop_Tool_Scanner.fbx"
        },
        {
            "pattern": r"^(?P<category>[^_]+)_(?P<name>[^_]+)\.(?P<ext>\w+)$",
            "path_template": "{category}/{name}.{ext}",
            "example": "Audio_Ambient.wav"
        }
    ]


@pytest.mark.parametrize("filename,expected", [
    ("GameCore_Character_Hero_Idle.fbx", {"module": "GameCore", "category": "Character", "feature": "Hero"}),
    ("Activity_UiEffect_LevelUp.png", {"module": "Activity", "category": "UiEffect", "feature": "LevelUp"}),
])
def test_single_rule_parse(single_rule, filename, expected):
    result = parse_filename(filename, single_rule)
    assert result is not None
    assert result["groups"]["module"] == expected["module"]
    assert result["groups"]["category"] == expected["category"]
    assert result["groups"]["feature"] == expected["feature"]


def test_multi_rule_four_layer(multi_rules):
    result = parse_filename("Character_Monster_Clicker_Idle.fbx", multi_rules)
    assert result is not None
    assert result["groups"]["category"] == "Character"
    assert result["groups"]["type"] == "Monster"
    assert result["groups"]["name"] == "Clicker"
    assert result["groups"]["variant"] == "Idle"
    assert result["path_template"] == "{category}/{type}/{name}_{variant}.{ext}"


def test_multi_rule_three_layer(multi_rules):
    result = parse_filename("Prop_Tool_Scanner.fbx", multi_rules)
    assert result is not None
    assert result["groups"]["category"] == "Prop"
    assert result["groups"]["type"] == "Tool"
    assert result["groups"]["name"] == "Scanner"
    assert result["path_template"] == "{category}/{type}/{name}.{ext}"


def test_multi_rule_two_layer(multi_rules):
    result = parse_filename("Audio_Ambient.wav", multi_rules)
    assert result is not None
    assert result["groups"]["category"] == "Audio"
    assert result["groups"]["name"] == "Ambient"
    assert result["path_template"] == "{category}/{name}.{ext}"


def test_no_match_returns_none(multi_rules):
    result = parse_filename("Invalid.fbx", multi_rules)
    assert result is None

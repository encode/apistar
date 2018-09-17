from apistar.validate.tokenize_json import tokenize_json
from apistar.validate.tokens import DictToken, ListToken, ScalarToken


def test_tokenize_object():
    token = tokenize_json('{"a": [1, 2, 3], "b": "test"}')
    expected = DictToken({
        ScalarToken('a', 1, 3): ListToken([
            ScalarToken(1, 7, 7),
            ScalarToken(2, 10, 10),
            ScalarToken(3, 13, 13)
        ], 6, 14),
        ScalarToken('b', 17, 19): ScalarToken('test', 22, 27)
    }, 0, 28)
    assert token == expected
    assert token.get_value() == {"a": [1, 2, 3], "b": "test"}
    assert token["a"].get_value() == [1, 2, 3]
    assert token["a"].start_index == 6
    assert token["a"].end_index == 14
    assert token["a"].start.line_no == 1
    assert token["a"].start.column_no == 7
    assert token.get_key("a").get_value() == "a"
    assert token.get_key("a").start_index == 1
    assert token.get_key("a").end_index == 3


def test_tokenize_list():
    token = tokenize_json('[true, false, null]')
    expected = ListToken([
        ScalarToken(True, 1, 4),
        ScalarToken(False, 7, 11),
        ScalarToken(None, 14, 17),
    ], 0, 18)
    assert token == expected
    assert token.get_value() == [True, False, None]
    assert token[0].get_value()
    assert token[0].start_index == 1
    assert token[0].end_index == 4


def test_tokenize_floats():
    token = tokenize_json('[100.0, 1.0E+2, 1E+2]')
    expected = ListToken([
        ScalarToken(100.0, 1, 5),
        ScalarToken(100.0, 8, 13),
        ScalarToken(100.0, 16, 19),
    ], 0, 20)
    assert token == expected
    assert token.get_value() == [100.0, 1.0E+2, 1E+2]
    assert token[0].get_value() == 100.0
    assert token[0].start_index == 1
    assert token[0].end_index == 5


def test_tokenize_whitespace():
    token = tokenize_json('{ }')
    expected = DictToken({}, 0, 2)
    assert token == expected
    assert token.get_value() == {}

    token = tokenize_json('{ "a" :  1 }')
    expected = DictToken({
        ScalarToken('a', 2, 4): ScalarToken(1, 9, 9)
    }, 0, 11)
    assert token == expected
    assert token.get_value() == {"a": 1}
    assert token["a"].get_value() == 1
    assert token["a"].start_index == 9
    assert token["a"].end_index == 9
    assert token.get_key("a").get_value() == "a"
    assert token.get_key("a").start_index == 2
    assert token.get_key("a").end_index == 4

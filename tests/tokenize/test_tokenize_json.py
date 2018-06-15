from apistar.tokenize import DictToken, ListToken, ScalarToken, tokenize_json


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


def test_tokenize_list():
    token = tokenize_json('[true, false, null]')
    expected = ListToken([
        ScalarToken(True, 1, 4),
        ScalarToken(False, 7, 11),
        ScalarToken(None, 14, 17),
    ], 0, 18)
    assert token == expected


def test_tokenize_floats():
    token = tokenize_json('[100.0, 1.0E+2, 1E+2]')
    expected = ListToken([
        ScalarToken(100.0, 1, 5),
        ScalarToken(100.0, 8, 13),
        ScalarToken(100.0, 16, 19),
    ], 0, 20)
    assert token == expected


def test_tokenize_whitespace():
    token = tokenize_json('{ }')
    expected = DictToken({}, 0, 2)
    assert token == expected

    token = tokenize_json('{ "a" :  1 }')
    expected = DictToken({
        ScalarToken('a', 2, 4): ScalarToken(1, 9, 9)
    }, 0, 11)
    assert token == expected

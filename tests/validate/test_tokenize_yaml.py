from apistar.validate.tokenize_yaml import tokenize_yaml
from apistar.validate.tokens import DictToken, ListToken, ScalarToken

YAML_OBJECT = '''
a:
  - 1
  - 2
  - 3
b: "test"
'''

YAML_LIST = '''
- true
- false
- null
'''

YAML_FLOATS = '''
- 100.0
- 1.0E+2
'''


def test_tokenize_object():
    token = tokenize_yaml(YAML_OBJECT)
    expected = DictToken({
        ScalarToken('a', 1, 1): ListToken([
            ScalarToken(1, 8, 8),
            ScalarToken(2, 14, 14),
            ScalarToken(3, 20, 20)
        ], 6, 21),
        ScalarToken('b', 22, 22): ScalarToken('test', 25, 30)
    }, 1, 31)
    assert token == expected


def test_tokenize_list():
    token = tokenize_yaml(YAML_LIST)
    expected = ListToken([
        ScalarToken(True, 3, 6),
        ScalarToken(False, 10, 14),
        ScalarToken(None, 18, 21),
    ], 1, 22)
    assert token == expected


def test_tokenize_floats():
    token = tokenize_yaml(YAML_FLOATS)
    expected = ListToken([
        ScalarToken(100.0, 3, 7),
        ScalarToken(100.0, 11, 16),
    ], 1, 17)
    assert token == expected

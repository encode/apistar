import pytest

from apistar import validators
from apistar.exceptions import (
    ErrorMessage, Marker, ParseError, ValidationError
)
from apistar.parse import parse_json

VALIDATOR = validators.Object(
    properties={
        'a': validators.Integer()
    },
    required=['a'],
    additional_properties=False
)


def test_empty_string():
    with pytest.raises(ParseError) as exc:
        parse_json(b'', VALIDATOR)

    error_messages = exc.value.get_error_messages()
    expecting = [
        ErrorMessage('No content.', Marker(0))
    ]
    assert error_messages == expecting


def test_object_missing_property_name():
    with pytest.raises(ParseError) as exc:
        parse_json('{', VALIDATOR)

    error_messages = exc.value.get_error_messages()
    expecting = [
        ErrorMessage('Expecting property name enclosed in double quotes.', Marker(1))
    ]
    assert error_messages == expecting


def test_object_missing_colon_delimiter():
    with pytest.raises(ParseError) as exc:
        parse_json('{"abc"', VALIDATOR)

    error_messages = exc.value.get_error_messages()
    expecting = [
        ErrorMessage("Expecting ':' delimiter.", Marker(6))
    ]
    assert error_messages == expecting


def test_object_missing_comma_delimiter():
    with pytest.raises(ParseError) as exc:
        parse_json('{"abc": "def" 1', VALIDATOR)

    error_messages = exc.value.get_error_messages()
    expecting = [
        ErrorMessage("Expecting ',' delimiter.", Marker(14))
    ]
    assert error_messages == expecting


def test_object_invalid_property_name():
    with pytest.raises(ParseError) as exc:
        parse_json('{"abc": "def", 1', VALIDATOR)

    error_messages = exc.value.get_error_messages()
    expecting = [
        ErrorMessage("Expecting property name enclosed in double quotes.", Marker(15))
    ]
    assert error_messages == expecting


def test_object_unterminated_after_key():
    with pytest.raises(ParseError) as exc:
        parse_json('{"abc": ', VALIDATOR)

    error_messages = exc.value.get_error_messages()
    expecting = [
        ErrorMessage("Expecting value.", Marker(8))
    ]
    assert error_messages == expecting


def test_object_unterminated_after_value():
    with pytest.raises(ParseError) as exc:
        parse_json('{"abc": "def"', VALIDATOR)

    error_messages = exc.value.get_error_messages()
    expecting = [
        ErrorMessage("Expecting ',' delimiter.", Marker(13))
    ]
    assert error_messages == expecting


def test_valid_json():
    parse_json('{"abc": "def"}')


def test_invalid_token():
    with pytest.raises(ParseError) as exc:
        parse_json('-', VALIDATOR)

    error_messages = exc.value.get_error_messages()
    expecting = [
        ErrorMessage("Expecting value.", Marker(0))
    ]
    assert error_messages == expecting


def test_invalid_top_level_item():
    with pytest.raises(ValidationError) as exc:
        parse_json('123', VALIDATOR)

    error_messages = exc.value.get_error_messages()
    expecting = [
        ErrorMessage('Must be an object.', Marker(0))
    ]
    assert error_messages == expecting


def test_invalid_property():
    with pytest.raises(ValidationError) as exc:
        parse_json('{"a": "abc"}', VALIDATOR)

    error_messages = exc.value.get_error_messages()
    expecting = [
        ErrorMessage('Must be a number.', Marker(6))
    ]
    assert error_messages == expecting


def test_invalid_properties():
    with pytest.raises(ValidationError) as exc:
        parse_json('{"a": "abc", "b": 123}', VALIDATOR)

    error_messages = exc.value.get_error_messages()
    expecting = [
        ErrorMessage('Must be a number.', Marker(6)),
        ErrorMessage('Invalid property name.', Marker(13))
    ]
    assert error_messages == expecting

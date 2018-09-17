import pytest

from apistar import validators
from apistar.exceptions import (
    ErrorMessage, ParseError, Position, ValidationError
)
from apistar.validate import validate


def test_valid_json():
    validate('{"abc": "def"}', format='json')


def test_empty_string():
    with pytest.raises(ParseError) as exc:
        validate(b'', format='json')

    assert exc.value.messages == [
        ErrorMessage(
            text='No content.',
            code='parse_error',
            position=Position(line_no=1, column_no=1, index=0)
        )
    ]


def test_object_missing_property_name():
    with pytest.raises(ParseError) as exc:
        validate('{', format='json')

    assert exc.value.messages == [
        ErrorMessage(
            text='Expecting property name enclosed in double quotes.',
            code='parse_error',
            position=Position(line_no=1, column_no=2, index=1)
        )
    ]


def test_object_missing_colon_delimiter():
    with pytest.raises(ParseError) as exc:
        validate('{"abc"', format='json')

    assert exc.value.messages == [
        ErrorMessage(
            text="Expecting ':' delimiter.",
            code='parse_error',
            position=Position(line_no=1, column_no=7, index=6)
        )
    ]


def test_object_missing_comma_delimiter():
    with pytest.raises(ParseError) as exc:
        validate('{"abc": "def" 1', format='json')

    assert exc.value.messages == [
        ErrorMessage(
            text="Expecting ',' delimiter.",
            code='parse_error',
            position=Position(line_no=1, column_no=15, index=14)
        )
    ]


def test_object_invalid_property_name():
    with pytest.raises(ParseError) as exc:
        validate('{"abc": "def", 1', format='json')

    assert exc.value.messages == [
        ErrorMessage(
            text="Expecting property name enclosed in double quotes.",
            code='parse_error',
            position=Position(line_no=1, column_no=16, index=15)
        )
    ]


def test_object_unterminated_after_key():
    with pytest.raises(ParseError) as exc:
        validate('{"abc": ', format='json')

    assert exc.value.messages == [
        ErrorMessage(
            text="Expecting value.",
            code='parse_error',
            position=Position(line_no=1, column_no=9, index=8)
        )
    ]


def test_object_unterminated_after_value():
    with pytest.raises(ParseError) as exc:
        validate('{"abc": "def"', format='json')

    assert exc.value.messages == [
        ErrorMessage(
            text="Expecting ',' delimiter.",
            code='parse_error',
            position=Position(line_no=1, column_no=14, index=13)
        )
    ]


def test_invalid_token():
    with pytest.raises(ParseError) as exc:
        validate('-', format='json')

    assert exc.value.messages == [
        ErrorMessage(
            text="Expecting value.",
            code='parse_error',
            position=Position(line_no=1, column_no=1, index=0)
        )
    ]


def test_unterminated_string():
    with pytest.raises(ParseError) as exc:
        validate('"ab', format='json')

    assert exc.value.messages == [
        ErrorMessage(
            text="Unterminated string.",
            code='parse_error',
            position=Position(line_no=1, column_no=1, index=0)
        )
    ]


VALIDATOR = validators.Object(
    properties={
        'a': validators.Integer()
    },
    required=['a'],
    additional_properties=False
)


def test_invalid_top_level_item():
    with pytest.raises(ValidationError) as exc:
        validate('123', format="json", schema=VALIDATOR)

    assert exc.value.messages == [
        ErrorMessage(
            text='Must be an object.',
            code='type',
            index=None,
            position=Position(line_no=1, column_no=1, index=0)
        )
    ]


def test_invalid_property():
    with pytest.raises(ValidationError) as exc:
        validate('{"a": "abc"}', format="json", schema=VALIDATOR)

    assert exc.value.messages == [
        ErrorMessage(
            text='Must be a number.',
            code='type',
            index=['a'],
            position=Position(line_no=1, column_no=7, index=6))
    ]


def test_invalid_properties():
    with pytest.raises(ValidationError) as exc:
        validate('{"a": "abc", "b": 123}', format="json", schema=VALIDATOR)

    assert exc.value.messages == [
        ErrorMessage(
            text='Must be a number.',
            code='type',
            index=['a'],
            position=Position(line_no=1, column_no=7, index=6)
        ),
        ErrorMessage(
            text='Invalid property name.',
            code='invalid_property',
            index=['b'],
            position=Position(line_no=1, column_no=14, index=13)
        )
    ]

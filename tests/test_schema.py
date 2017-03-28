from apistar import exceptions, schema


def schema_error(cls, value):
    try:
        cls(value)
    except exceptions.SchemaError as exc:
        return str(exc)
    return None


class ExampleInteger(schema.Integer):
    minimum = -3
    maximum = 3


def test_valid_integer():
    assert ExampleInteger(1) == 1


def test_integer_maximum():
    assert schema_error(ExampleInteger, 4) == 'Must be less than or equal to 3.'


def test_integer_minimum():
    assert schema_error(ExampleInteger, -4) == 'Must be greater than or equal to -3.'


def test_valid_integer_from_string():
    assert ExampleInteger('1') == 1


def test_invalid_integer_from_string():
    assert schema_error(ExampleInteger, '') == 'Must be a valid number.'


def test_integer_kwargs():
    schema = ExampleInteger(maximum=5)
    assert schema(4) == 4

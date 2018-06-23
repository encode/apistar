import pytest
from apistar import validators
from apistar import exceptions


def test_number_validator_enum_positive():
    v = validators.Number(enum=[0.1])
    assert v.validate(0.1) == 0.1


def test_number_validator_enum_negative():
    v = validators.Number(enum=[0.1])
    with pytest.raises(exceptions.ValidationError):
        v.validate(0.2)


def test_integer_validator_enum_positive():
    v = validators.Integer(enum=[0])
    assert v.validate(0) == 0


def test_integer_validator_enum_negative():
    v = validators.Integer(enum=[0])
    with pytest.raises(exceptions.ValidationError):
        v.validate(1)

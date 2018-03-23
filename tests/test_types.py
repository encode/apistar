import datetime

import pytest

from apistar import exceptions, types, validators
from apistar.utils import encode_jsonschema

utc = datetime.timezone.utc


class Product(types.Type):
    name = validators.String(max_length=10)
    rating = validators.Integer(allow_null=True, default=None, minimum=0, maximum=100)
    created = validators.DateTime()


class Instance():
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_from_object():
    when = datetime.datetime(2020, 1, 1, 12, 0, 0, tzinfo=utc)
    instance = Instance(name='abc', rating=20, created=when)
    product = Product(instance)

    assert product.name == 'abc'
    assert product.rating == 20
    assert product.created == when
    assert dict(product) == {
        'name': 'abc',
        'rating': 20,
        'created': '2020-01-01T12:00:00Z'
    }


def test_from_kwargs():
    when = datetime.datetime(2020, 1, 1, 12, 0, 0, tzinfo=utc)
    product = Product(name='abc', rating=20, created=when)

    assert product.name == 'abc'
    assert product.rating == 20
    assert product.created == when
    assert dict(product) == {
        'name': 'abc',
        'rating': 20,
        'created': '2020-01-01T12:00:00Z'
    }


def test_from_dict():
    when = datetime.datetime(2020, 1, 1, 12, 0, 0, tzinfo=utc)
    product = Product({'name': 'abc', 'rating': 20, 'created': when})

    assert product.name == 'abc'
    assert product.rating == 20
    assert product.created == when
    assert dict(product) == {
        'name': 'abc',
        'rating': 20,
        'created': '2020-01-01T12:00:00Z'
    }


def test_setattr():
    when = datetime.datetime(2020, 1, 1, 12, 0, 0, tzinfo=utc)
    product = Product(name='abc', rating=20, created=when)

    assert product.name == 'abc'
    assert product.rating == 20
    assert product.created == when
    assert dict(product) == {
        'name': 'abc',
        'rating': 20,
        'created': '2020-01-01T12:00:00Z'
    }

    # Set a format field, using a native type.
    product.created = datetime.datetime(2030, 2, 2, 13, 30, 0, tzinfo=utc)
    assert dict(product) == {
        'name': 'abc',
        'rating': 20,
        'created': '2030-02-02T13:30:00Z'
    }

    # Set format field, using a string.
    product.created = '2040-03-03T15:45:00Z'
    assert dict(product) == {
        'name': 'abc',
        'rating': 20,
        'created': '2040-03-03T15:45:00Z'
    }

    # Set with an invalid value.
    with pytest.raises(exceptions.ValidationError) as exc:
        product.name = None
    assert exc.value.detail == 'May not be null.'


def test_setitem():
    when = datetime.datetime(2020, 1, 1, 12, 0, 0, tzinfo=utc)
    product = Product(name='abc', rating=20, created=when)

    assert product.name == 'abc'
    assert product.rating == 20
    assert product.created == when
    assert dict(product) == {
        'name': 'abc',
        'rating': 20,
        'created': '2020-01-01T12:00:00Z'
    }

    # Set a format field, using a native type.
    product['created'] = datetime.datetime(2030, 2, 2, 13, 30, 0, tzinfo=utc)
    assert dict(product) == {
        'name': 'abc',
        'rating': 20,
        'created': '2030-02-02T13:30:00Z'
    }

    # Set format field, using a string.
    product['created'] = '2040-03-03T15:45:00Z'
    assert dict(product) == {
        'name': 'abc',
        'rating': 20,
        'created': '2040-03-03T15:45:00Z'
    }

    # Set with an invalid value.
    with pytest.raises(exceptions.ValidationError) as exc:
        product['name'] = None
    assert exc.value.detail == 'May not be null.'


def test_misc():
    when = datetime.datetime(2020, 1, 1, 12, 0, 0, tzinfo=utc)
    instance = Instance(name='abc', rating=20, created=when)
    product = Product(instance)

    assert len(product) == 3
    assert repr(product) == "<Product(name='abc', rating=20, created='2020-01-01T12:00:00Z')>"
    assert len(product._dict) == 3
    assert list(product.keys()) == ['name', 'rating', 'created']
    with pytest.raises(AttributeError):
        product.other = 456
    with pytest.raises(KeyError):
        product['other'] = 456
    with pytest.raises(exceptions.ValidationError):
        Product([])


def test_reserved_keys():
    with pytest.raises(exceptions.ConfigurationError):
        class Something(types.Type):
            keys = validators.String()


def test_as_jsonschema():
    struct = encode_jsonschema(Product, to_data_structure=True)
    assert struct == {
        "$ref": "#/definitions/Product",
        "definitions": {
            "Product": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "maxLength": 10
                    },
                    "rating": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                        "default": None,
                        "nullable": True
                    },
                    "created": {
                        "type": "string",
                        "format": "datetime"
                    }
                },
                "required": [
                    "name",
                    "created"
                ]
            }
        }
    }

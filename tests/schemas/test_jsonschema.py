import json
import os

import pytest

from apistar import types, validators
from apistar.schemas.jsonschema import JSONSchema

filenames = [
    "additionalItems.json",
    "additionalProperties.json",
    # 'allOf.json',
    # 'anyOf.json',
    "default.json",
    # 'definitions.json',
    # 'dependencies.json',
    # 'enum.json',
    "items.json",
    "maxItems.json",
    "maxLength.json",
    "maxProperties.json",
    "maximum.json",
    "minItems.json",
    "minLength.json",
    "minProperties.json",
    "minimum.json",
    "multipleOf.json",
    # 'not.json',
    # 'oneOf.json',
    "pattern.json",
    "patternProperties.json",
    "properties.json",
    # 'ref.json',
    # 'refRemote.json',
    "required.json",
    "type.json",
    "uniqueItems.json",
]


def load_test_cases():
    loaded = []

    for filename in filenames:
        path = os.path.join("testcases", "jsonschema", filename)
        content = open(path, "rb").read()
        test_suite = json.loads(content.decode("utf-8"))
        for test_cases in test_suite:
            description = test_cases["description"]
            schema = test_cases["schema"]
            for test in test_cases["tests"]:
                test_description = test["description"]
                test_data = test["data"]
                test_valid = test["valid"]
                full_description = "%s : %s - %s" % (
                    filename,
                    description,
                    test_description,
                )
                case = (schema, test_data, test_valid, full_description)
                loaded.append(case)

    return loaded


test_cases = load_test_cases()


@pytest.mark.parametrize("schema,value,is_valid,description", test_cases)
def test_json_schema(schema, value, is_valid, description):
    validator = JSONSchema().decode_from_data_structure(schema)
    was_valid = validator.is_valid(value)
    assert was_valid == is_valid, description


class Product(types.Type):
    name = validators.String(max_length=10)
    rating = validators.Integer(allow_null=True, default=None, minimum=0, maximum=100)
    created = validators.DateTime()


class ReviewedProduct(Product):
    reviewer = validators.String(max_length=20)


def test_as_jsonschema():
    codec = JSONSchema()
    struct = codec.encode(Product, to_data_structure=True)
    assert struct == {
        "$ref": "#/definitions/Product",
        "definitions": {
            "Product": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "maxLength": 10},
                    "rating": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                        "default": None,
                        "nullable": True,
                    },
                    "created": {"type": "string", "format": "datetime"},
                },
                "required": ["name", "created"],
            }
        },
    }


def test_extended_as_jsonschema_flat():
    codec = JSONSchema()
    struct = codec.encode(ReviewedProduct, to_data_structure=True)
    assert struct == {
        "$ref": "#/definitions/ReviewedProduct",
        "definitions": {
            "ReviewedProduct": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "maxLength": 10},
                    "rating": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                        "default": None,
                        "nullable": True,
                    },
                    "created": {"type": "string", "format": "datetime"},
                    "reviewer": {"type": "string", "maxLength": 20},
                },
                "required": ["name", "created", "reviewer"],
            }
        },
    }

import pytest

from apistar import validators
from apistar.core import validate
from apistar.exceptions import (
    ErrorMessage, ParseError, Position, ValidationError
)


def test_validate_openapi():
    schema = """
    {
        "openapi": "3.0.0",
        "info": {"title": "", "version": ""},
        "paths": {}
    }
    """
    validate(schema, format="openapi")


def test_validate_openapi_datastructure():
    schema = {
        "openapi": "3.0.0",
        "info": {"title": "", "version": ""},
        "paths": {}
    }
    validate(schema, format="openapi")


def test_validate_autodetermine_openapi():
    schema = """
    {
        "openapi": "3.0.0",
        "info": {"title": "", "version": ""},
        "paths": {}
    }
    """
    validate(schema)


def test_validate_autodetermine_swagger():
    schema = """
    {
        "swagger": "2.0",
        "info": {"title": "", "version": ""},
        "paths": {}
    }
    """
    validate(schema)


def test_validate_autodetermine_failed():
    schema = """
    {
        "info": {"title": "", "version": ""},
        "paths": {}
    }
    """
    with pytest.raises(ValidationError):
        validate(schema)


def test_validate_with_bad_format():
    schema = """
    {
        "openapi": "3.0.0",
        "info": {"title": "", "version": ""},
        "paths": {}
    }
    """
    with pytest.raises(ValueError):
        validate(schema, format="xxx")


def test_validate_with_bad_base_format():
    schema = """
    {
        "openapi": "3.0.0",
        "info": {"title": "", "version": ""},
        "paths": {}
    }
    """
    with pytest.raises(ValueError):
        validate(schema, format="openapi", base_format="xxx")

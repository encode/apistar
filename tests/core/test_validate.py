import pytest

from apistar.core import validate
from apistar.exceptions import ValidationError


def test_validate_openapi():
    schema = """
    {
        "openapi": "3.0.0",
        "info": {"title": "", "version": ""},
        "paths": {}
    }
    """
    validate(schema, format="openapi", encoding="json")


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
    validate(schema, encoding="json")


def test_validate_autodetermine_swagger():
    schema = """
    {
        "swagger": "2.0",
        "info": {"title": "", "version": ""},
        "paths": {}
    }
    """
    validate(schema, encoding="json")


def test_validate_autodetermine_failed():
    schema = """
    {
        "info": {"title": "", "version": ""},
        "paths": {}
    }
    """
    with pytest.raises(ValidationError):
        validate(schema, encoding="json")


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


def test_validate_with_bad_encoding():
    schema = """
    {
        "openapi": "3.0.0",
        "info": {"title": "", "version": ""},
        "paths": {}
    }
    """
    with pytest.raises(ValueError):
        validate(schema, format="openapi", encoding="xxx")


def test_validate_missing_encoding():
    """
    Omitting 'encoding=' is invalid if 'schema' is a string/bytestring.
    """
    schema = """
    {
        "openapi": "3.0.0",
        "info": {"title": "", "version": ""},
        "paths": {}
    }
    """
    with pytest.raises(ValueError):
        validate(schema, format="openapi")


def test_validate_unneccessary_encoding():
    """
    Passing 'encoding=' is invalid if 'schema' is a dict already.
    """
    schema = {
        "openapi": "3.0.0",
        "info": {"title": "", "version": ""},
        "paths": {}
    }
    with pytest.raises(ValueError):
        validate(schema, format="openapi", encoding="json")

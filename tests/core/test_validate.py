import pytest

from apistar.core import validate
import typesystem


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
    schema = {"openapi": "3.0.0", "info": {"title": "", "version": ""}, "paths": {}}
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
    with pytest.raises(typesystem.ValidationError):
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


def test_infer_json():
    """
    If 'encoding=' is omitted, then it should inferred from the content.
    """
    schema = """
    {
        "openapi": "3.0.0",
        "info": {"title": "", "version": ""},
        "paths": {}
    }
    """
    validate(schema, format="openapi")


def test_infer_yaml():
    """
    If 'encoding=' is omitted, then it should inferred from the content.
    """
    schema = """
        openapi: "3.0.0"
        info:
            title: ""
            version: ""
        paths: {}
    """
    validate(schema, format="openapi")

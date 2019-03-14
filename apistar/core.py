import os
import re
import typing

import jinja2

from apistar.schemas.autodetermine import AUTO_DETERMINE
from apistar.schemas.config import APISTAR_CONFIG
from apistar.schemas.jsonschema import JSON_SCHEMA
from apistar.schemas.openapi import OPEN_API, OpenAPI
from apistar.schemas.swagger import SWAGGER, Swagger

import typesystem


FORMAT_CHOICES = ["config", "jsonschema", "openapi", "swagger", None]
ENCODING_CHOICES = ["json", "yaml", None]

# The regexs give us a best-guess for the encoding if none is specified.
# They check to see if the document looks like it is probably a YAML object or
# probably a JSON object. It'll typically be best to specify the encoding
# explicitly, but this should do for convenience.
INFER_YAML = re.compile(r"^([ \t]*#.*\n|---[ \t]*\n)*\s*[A-Za-z0-9_-]+[ \t]*:")
INFER_JSON = re.compile(r'^\s*{\s*"[A-Za-z0-9_-]+"\s*:')


def validate(schema: typing.Union[dict, str, bytes], format: str=None, encoding: str=None):
    if not isinstance(schema, (dict, str, bytes)):
        raise ValueError(f"schema must be either str, bytes, or dict.")
    if format not in FORMAT_CHOICES:
        raise ValueError(f"format must be one of {FORMAT_CHOICES!r}")
    if encoding not in ENCODING_CHOICES:
        raise ValueError(f"encoding must be one of {ENCODING_CHOICES!r}")

    if isinstance(schema, bytes):
        schema = schema.decode("utf8", "ignore")

    if isinstance(schema, str):
        if encoding is None:
            if INFER_YAML.match(schema):
                encoding = "yaml"
            elif INFER_JSON.match(schema):
                encoding = "json"
            else:
                text = "Could not determine if content is JSON or YAML."
                code = "unknown_encoding"
                position = typesystem.Position(line_no=1, column_no=1, char_index=0)
                raise typesystem.ParseError(text=text, code=code, position=position)

        tokenize = {
            "yaml": typesystem.tokenize_yaml,
            "json": typesystem.tokenize_json
        }[encoding]
        token = tokenize(schema)
        value = token.value
    else:
        token = None
        value = schema

    if format is None:
        if "openapi" in value and "swagger" not in value:
             format = "openapi"
        elif "swagger" in value and "openapi" not in value:
             format = "swagger"

    validator = {
        "config": APISTAR_CONFIG,
        "jsonschema": JSON_SCHEMA,
        "openapi": OPEN_API,
        "swagger": SWAGGER,
        None: AUTO_DETERMINE
    }[format]

    if token is not None:
        value = typesystem.validate_with_positions(token=token, validator=validator)
    else:
        value = validator.validate(value)

    if format is None:
        format = "swagger" if "swagger" in value else "openapi"

    if format == "swagger":
        return Swagger().load(value)
    elif format == "openapi":
        return OpenAPI().load(value)
    return value


def docs(
    schema,
    format=None,
    encoding=None,
    theme="apistar",
    schema_url=None,
    static_url=None,
):
    if format not in [None, "openapi", "swagger"]:
        raise ValueError('format must be either "openapi" or "swagger"')

    document = validate(schema, format=format, encoding=encoding)

    loader = jinja2.PrefixLoader(
        {
            theme: jinja2.PackageLoader(
                "apistar", os.path.join("themes", theme, "templates")
            )
        }
    )
    env = jinja2.Environment(autoescape=True, loader=loader)

    if static_url is None:

        def static_url_func(path):
            return "/" + path.lstrip("/")

    elif isinstance(static_url, str):

        def static_url_func(path):
            return static_url.rstrip("/") + "/" + path.lstrip("/")

    else:
        static_url_func = static_url

    template = env.get_template(theme + "/index.html")
    return template.render(
        document=document,
        langs=["javascript", "python"],
        code_style=None,
        static_url=static_url_func,
        schema_url=schema_url,
    )

# API Documentation

API Star can build API documentation from an OpenAPI or Swagger schema.
It supports a number of different themes, and the command line tool allows you
to preview the documentation as you edit the schema.

```script
$ apistar docs --path schema.json --format openapi`
✓ Documentation built at "build/index.html".
```

## Configuration

Configure the defaults for `apistar docs` using an `apistar.yml` file.

```yaml
schema:
    path: schema.json
    format: openapi
docs:
    output_dir: docs
    theme: apistar
```

Now you can build the documentation like so:

```shell
$ apistar docs
✓ Documentation built at "docs/index.html".
```

The documentation is a static HTML build and can be hosted anywhere.

## Previewing the API documentation

To preview the API documentation use `apistar docs --serve`, which will
build the documentation, and then start up a webserver.

```shell
$ apistar docs --serve
✓ Documentation available at "http://127.0.0.1:8000/" (Ctrl+C to quit)
```

## Programmatic interface

You can also build API documentation using a programmatic interface.
This allows you to dynamically serve API documentation from any Python web
server that is able to generate an OpenAPI or Swagger specification.

```python
import apistar


schema = """
openapi: 3.0.0
info:
  title: Widget API
  version: '1.0'
  description: An example API for widgets
paths:
  /widgets:
    get:
      summary: List all the widgets.
      operationId: listWidgets
      parameters:
      - in: query
        name: search
        description: Filter widgets by this search term.
        schema:
          type: string
"""

index_html = apistar.docs(schema, schema_url='/schema.yaml', static_url='/static/')
```

If you're serving the documentation dynamically, then you'll also need to make
sure that your framework serves up the API schema, and the static media for the
documentation theme.

Function signature: `docs(schema, format=None, encoding=None, theme="apistar", schema_url=None, static_url=None)`

* `schema` - Either a dict representing the schema, or a string/bytestring.
* `format` - One of `"openapi"` or `"swagger"`. If unset, this will be inferred from the schema.
If unset, one of either `openapi` or `swagger` will be inferred from the content if possible.
* `encoding` - If schema is passed as a string/bytestring then the encoding may be
specified as either "json" or "yaml". If not included, the encoding will be inferred from the content if possible.
* `theme` - One of `"apistar"`, `"swaggerui"`, or `"redoc"`.
* `schema_url` - The URL for the schema file, as a string. Required for `swaggerui` and `redoc`.
* `static_url` - The prefix for the static files, as a string. For more complex cases, this can also
be passed as a function that takes a string path, and returns a string URL.

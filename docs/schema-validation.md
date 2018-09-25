# Schema validation

You can use API Star to validate your API Schema. When errors occur it'll
give you a full breakdown of exactly where the schema is incorrect.

```shell
$ apistar validate --path schema.json --format openapi
✓ Valid OpenAPI schema.
```

## Configuration

Configure the defaults for `apistar validate` using an `apistar.yml` file.

```yaml
schema:
    path: schema.json
    format: openapi
```

You can now run the validation like so:

```shell
$ apistar validate
✓ Valid OpenAPI schema.
```

## Programmatic interface

You can also run the schema validation programmatically:

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

apistar.validate(schema, format='openapi', encoding="yaml")
```

Function signature: `validate(schema, format=None, encoding=None)`

* `schema` - Either a dict representing the schema, or a string/bytestring.
* `format` - One of `openapi`, `swagger`, `jsonschema` or `config`.
If unset, one of either `openapi` or `swagger` will be inferred from the content if possible.
* `encoding` - If schema is passed as a string/bytestring then the encoding may be
specified as either "json" or "yaml".  If unset, it will be inferred from the content if possible.

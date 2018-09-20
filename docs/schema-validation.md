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

apistar.validate(schema, format='openapi')
```

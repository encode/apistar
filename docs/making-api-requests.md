# Making API requests

The APIStar client library allows you to make requests to an API, given an API Schema.

Here's an example of how an API request might look:

```shell
$ apistar request listWidgets search=cogwheel --path schema.yml
[
    {
        "name": "Small cogwheel.",
        "productId": 24325,
        "inStock": true
    },
    {
        "name": "Large cogwheel.",
        "productId": 24326,
        "inStock": true
    }
]
```

## Configuration

To make an API request you'll normally want to make sure you have an
`apistar.yml` configuration file which references the API schema.

This will save you from having to include the schema path on every request.

```yaml
schema:
    path: schema.yml
    format: openapi
```

We can now make the request more simply, as:

```shell
$ apistar request listWidgets search=cogwheel
[
    {
        "name": "Small cogwheel.",
        "productId": 24325,
        "inStock": true
    },
    {
        "name": "Large cogwheel.",
        "productId": 24326,
        "inStock": true
    }
]
```

## Programmatic interface

You can make requests against an API using [the API Star client library](client-library.md).

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

client = apistar.Client(schema, format='openapi', encoding="yaml")
results = client.request('listWidgets', search="cogwheel")
```

See [the client library documentation](client-library.md) for more details.

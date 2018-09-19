# Documentation

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

## Programmatic interface

You can also build API documentation using a programmatic interface.
This allows you to dynamically serve API documentation from any Python web
server that is able to generate an OpenAPI or Swagger specification.

```python
import apistar


schema = {
    "openapi": "3.0.0",
    "info": {
        "title": "Widget API",
        "version": "1.0",
        "description": "An example API for widgets"
    },
    "paths": {
        "/widgets": {
            "get": {
                "summary": "List all the widgets.",
                "parameters": [
                    {
                        "in": "query",
                        "name": "search",
                        "description": "Filter widgets by this search term.",
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
            }
        }
    }
}

index_html = apistar.docs(schema)
```

If you're serving the documentation dynamically, then you'll also need to make
sure that your framework serves up the schema, and the static media for the
documentation theme.

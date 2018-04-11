# API Schemas

By default API Star will serve [an Open API schema][openapi] for your
application, at `'/schema/'`.

Let's take a look at that with a short example...

```python
from apistar import App, Route


def welcome(name=None):
    if name is None:
        return {'message': 'Welcome to API Star!'}
    return {'message': 'Welcome to API Star, %s!' % name}

routes = [
    Route('/', method='GET', handler=welcome),
]

app = App(routes=routes)


if __name__ == '__main__':
    app.serve('127.0.0.1', 8080, use_debugger=True)
```

Start the application running...

```bash
$ python ./example.py
 * Running on http://127.0.0.1:8080/ (Press CTRL+C to quit)
```

And download the schema...

```bash
$ curl http://127.0.0.1:8080/schema/
{
    "openapi": "3.0.0",
    "info": {
        "title": "",
        "description": "",
        "version": ""
    },
    "paths": {
        "/": {
            "get": {
                "operationId": "welcome",
                "parameters": [
                    {
                        "name": "name",
                        "in": "query"
                    }
                ]
            }
        }
    }
}
```

You can disable the schema generation by using the `schema_url` argument.

```python
app = App(routes=routes, schema_url=None)
```

[openapi]: https://github.com/OAI/OpenAPI-Specification

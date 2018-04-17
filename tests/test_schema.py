from apistar import App, Route, TestClient, types, validators
from apistar.server.handlers import serve_schema


class User(types.Type):
    name = validators.String(max_length=100)
    age = validators.Integer(allow_null=True, default=None)


def get_endpoint(name: str, age: int=None):
    raise NotImplementedError()


def post_endpoint(user: User):
    raise NotImplementedError()


routes = [
    Route(url='/get-endpoint/', method='GET', handler=get_endpoint),
    Route(url='/post-endpoint/', method='POST', handler=post_endpoint),
    Route(url='/schema/', method='GET', handler=serve_schema, documented=False),
]
app = App(routes=routes)
test_client = TestClient(app)


expected_schema = """{
    "openapi": "3.0.0",
    "info": {
        "title": "",
        "description": "",
        "version": ""
    },
    "paths": {
        "/get-endpoint/": {
            "get": {
                "operationId": "get_endpoint",
                "parameters": [
                    {
                        "name": "name",
                        "in": "query",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "age",
                        "in": "query",
                        "schema": {
                            "type": "integer",
                            "default": null,
                            "nullable": true
                        }
                    }
                ]
            }
        },
        "/post-endpoint/": {
            "post": {
                "operationId": "post_endpoint",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/User"
                            }
                        }
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "User": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "maxLength": 100
                    },
                    "age": {
                        "default": null,
                        "nullable": true,
                        "type": "integer"
                    }
                },
                "required": [
                    "name"
                ]
            }
        }
    }
}"""


def test_get_schema():
    response = test_client.get('/schema/')
    assert response.status_code == 200
    assert response.text == expected_schema

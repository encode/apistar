from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

from apistar.client import Client

app = Starlette()


@app.route('/path-param/{value}')
def path_param(request, value):
    return JSONResponse({'value': value})


@app.route('/query-params/')
def query_params(request):
    return JSONResponse({'query': dict(request.query_params)})


@app.route('/body-param/', methods=['POST'])
async def body_param(request):
    data = await request.json()
    return JSONResponse({'body': dict(data)})


schema = {
    'openapi': '3.0.0',
    'info': {
        'title': 'Test API',
        'version': '1.0'
    },
    'servers': [{
        'url': 'http://testserver',
    }],
    'paths': {
        '/path-param/{value}': {
            'get': {
                'operationId': 'path-param',
                'parameters': [{
                    'name': 'value',
                    'in': 'path',
                    'required': True
                }]
            }
        },
        '/query-params/': {
            'get': {
                'operationId': 'query-params',
                'parameters': [{
                    'name': 'a',
                    'in': 'query'
                }, {
                    'name': 'b',
                    'in': 'query'
                }]
            }
        },
        '/body-param/': {
            'post': {
                'operationId': 'body-param',
                'requestBody': {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "example": {"type": "integer"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}


def test_path_param():
    client = Client(schema, session=TestClient(app))
    data = client.request('path-param', value=123)
    assert data == {'value': '123'}


def test_query_params():
    client = Client(schema, session=TestClient(app))
    data = client.request('query-params', a=123, b=456)
    assert data == {'query': {'a': '123', 'b': '456'}}


def test_body_param():
    client = Client(schema, session=TestClient(app))
    data = client.request('body-param', body={'example': 123})
    assert data == {'body': {'example': 123}}

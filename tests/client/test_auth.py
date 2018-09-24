from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

from apistar.client.auth import TokenAuthentication
from apistar.client import Client

app = Starlette()


@app.route('/token-auth')
def token_auth(request):
    return JSONResponse({'authorization': request.headers['Authorization']})


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
        '/token-auth': {
            'get': {
                'operationId': 'token-auth'
            }
        },
    }
}


def test_token_auth():
    session = TestClient(app)
    auth = TokenAuthentication('xxx')
    client = Client(schema, session=session, auth=auth)
    data = client.request('token-auth')
    assert data == {'authorization': 'Bearer xxx'}

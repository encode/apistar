import base64

import pytest

from apistar import Route, TestClient, http
from apistar.authentication import Authenticated
from apistar.frameworks.asyncio import ASyncIOApp
from apistar.frameworks.wsgi import WSGIApp
from apistar.interfaces import Auth


def get_auth(auth: Auth):
    return {
        'user_id': auth.get_user_id(),
        'display_name': auth.get_display_name(),
        'is_authenticated': auth.is_authenticated()
    }


class BasicAuthentication():
    def authenticate(self, authorization: http.Header):
        """
        Determine the user associated with a request, using HTTP Basic Authentication.
        """
        if authorization is None:
            return None

        scheme, token = authorization.split()
        if scheme.lower() != 'basic':
            return None

        username, password = base64.b64decode(token).decode('utf-8').split(':')
        return Authenticated(username)


routes = [
    Route('/auth/', 'GET', get_auth),
]
settings = {
    'AUTHENTICATION': [BasicAuthentication()]
}

wsgi_app = WSGIApp(routes=routes, settings=settings)
wsgi_client = TestClient(wsgi_app)

async_app = ASyncIOApp(routes=routes, settings=settings)
async_client = TestClient(async_app)


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_unauthenticated_request(client):
    response = client.get('http://example.com/auth/')
    assert response.json() == {
        'display_name': '',
        'user_id': '',
        'is_authenticated': False
    }


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_authenticated_request(client):
    response = client.get('http://example.com/auth/', auth=('tomchristie', 'password123'))
    assert response.json() == {
        'display_name': 'tomchristie',
        'user_id': 'tomchristie',
        'is_authenticated': True
    }

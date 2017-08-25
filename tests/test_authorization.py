import jwt
import pytest

from apistar import Route, Settings, TestClient, exceptions, http
from apistar.components.authorization import JWT, Token
from apistar.frameworks.asyncio import ASyncIOApp
from apistar.frameworks.wsgi import WSGIApp


def auth_required(request: http.Request, token: JWT):
    return token.payload


@pytest.mark.parametrize('app_class', [WSGIApp, ASyncIOApp])
def test_jwt(app_class) -> None:
    routes = [
        Route('/auth-required-route', 'GET', auth_required),
    ]
    settings = {
        'AUTHORIZATION': {'JWT_SECRET': 'jwt-secret'}
    }

    app = app_class(routes=routes, settings=settings)
    client = TestClient(app)

    response = client.get('/auth-required-route')
    assert response.status_code == 401

    payload = {'user': 1}
    secret = settings['AUTHORIZATION']['JWT_SECRET']
    encoded_jwt = jwt.encode(payload, secret)

    response = client.get('auth-required-route', headers={
        'Authorization': 'Basic',
    })
    assert response.status_code == 401

    response = client.get('/auth-required-route', headers={
        'Authorization': 'Bearer {token}'.format(token=encoded_jwt),
    })
    assert response.status_code == 200
    assert response.json() == payload

    encoded_jwt = jwt.encode(payload, 'wrong-secret')
    response = client.get('/auth-required-route', headers={
        'Authorization': 'Bearer {token}'.format(token=encoded_jwt),
    })
    assert response.status_code == 401


def test_misconfigured_jwt_settings() -> None:
    settings = Settings({
        'AUTHORIZATION': {},
    })
    with pytest.raises(exceptions.ConfigurationError):
        JWT(token=Token('abc'), settings=settings)

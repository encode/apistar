import jwt
import pytest

from apistar import Route, Settings, TestClient, exceptions, http
from apistar.components.authorization import (
    Algorithm, DecodedJWT, EncodedJWT, Token
)
from apistar.frameworks.asyncio import ASyncIOApp
from apistar.frameworks.wsgi import WSGIApp


def auth_required(request: http.Request, token: DecodedJWT):
    return token.payload


@pytest.mark.parametrize('app_class', [WSGIApp, ASyncIOApp])
def test_decoded_jwt(app_class) -> None:
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
    encoded_jwt = jwt.encode(payload, secret, algorithm='HS256').decode(encoding='UTF-8')

    response = client.get('/auth-required-route', headers={
        'Authorization': 'Bearer',
    })
    assert response.status_code == 401

    response = client.get('/auth-required-route', headers={
        'Authorization': 'Basic username',
    })
    assert response.status_code == 401

    response = client.get('/auth-required-route', headers={
        'Authorization': 'Bearer {token}'.format(token=encoded_jwt),
    })
    assert response.status_code == 200
    assert response.json() == payload

    encoded_jwt = jwt.encode(payload, 'wrong-secret').decode(encoding='UTF-8')
    response = client.get('/auth-required-route', headers={
        'Authorization': 'Bearer {token}'.format(token=encoded_jwt),
    })
    assert response.status_code == 401


def test_encoded_jwt() -> None:
    payload = {'email': 'test@example.com'}
    token = jwt.encode(payload, 'jwt-secret', algorithm='HS256').decode(encoding='UTF-8')
    settings = Settings({
        'AUTHORIZATION': {'JWT_SECRET': 'jwt-secret'}
    })

    encoded_jwt = EncodedJWT(payload=payload, settings=settings)
    assert encoded_jwt.token == token

    encoded_jwt = EncodedJWT(payload=payload, settings=settings, algorithm=Algorithm('HS512'))
    assert encoded_jwt.token != token
    token = jwt.encode(payload, 'jwt-secret', algorithm='HS512').decode(encoding='UTF-8')
    assert encoded_jwt.token == token


def test_misconfigured_jwt_settings() -> None:
    settings = Settings({
        'AUTHORIZATION': {},
    })
    token = Token('abc')
    payload = {'some': 'payload'}

    with pytest.raises(exceptions.ConfigurationError):
        DecodedJWT(token=token, settings=settings)
    with pytest.raises(exceptions.ConfigurationError):
        EncodedJWT(payload=payload, settings=settings)

    settings = Settings({
        'AUTHORIZATION': {'JWT_SECRET': 'jwt-secret', 'JWT_ALGORITHMS': ['unknown-algo']}
    })

    with pytest.raises(exceptions.ConfigurationError):
        EncodedJWT(payload=payload, settings=settings)

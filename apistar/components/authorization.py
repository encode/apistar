import typing

import jwt

from apistar import exceptions, http
from apistar.types import Settings

Token = typing.NewType('Token', str)


class JWT():
    DEFAULT_SETTINGS = {
        'JWT_ALGORITHMS': ['HS256'],
    }

    def __init__(self,
                 token: Token,
                 settings: Settings) -> None:
        authorization_settings = settings.get('AUTHORIZATION', self.DEFAULT_SETTINGS)
        secret = authorization_settings.get('JWT_SECRET', None)
        if secret is None:
            msg = 'The JWT_SECRET setting under AUTHORIZATION settings must be defined.'
            raise exceptions.ConfigurationError(msg) from None
        algorithms = authorization_settings.get('JWT_ALGORITHMS', ['HS256'])
        try:
            payload = jwt.decode(token, secret, algorithms=algorithms)
        except Exception:
            raise exceptions.AuthenticationFailed()
        self.payload = payload


def get_decoded_jwt(authorization: http.Header, settings: Settings):
    if authorization is None:
        raise exceptions.NotAuthenticated('Authorization header is missing.') from None
    try:
        scheme, token = authorization.split()
    except ValueError:
        raise exceptions.AuthenticationFailed('Could not seperate Authorization scheme and token.') from None
    if scheme.lower() != 'bearer':
        raise exceptions.AuthenticationFailed('Authorization scheme not supported, try Bearer') from None
    return JWT(token=Token(token), settings=settings)

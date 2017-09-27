import pytest

from apistar import Response, Route, TestClient, http
from apistar.frameworks.asyncio import ASyncIOApp
from apistar.frameworks.wsgi import WSGIApp


def homepage(session: http.Session):
    return {
        'username': session.get('username')
    }


def login(username: str, session: http.Session):
    session['username'] = username
    return Response(status=302, headers={'location': '/'})


def logout(session: http.Session):
    if 'username' in session:
        del session['username']
    return Response(status=302, headers={'location': '/'})


routes = [
    Route('/', 'GET', homepage),
    Route('/login', 'POST', login),
    Route('/logout', 'POST', logout),
]

wsgi_app = WSGIApp(routes=routes)
asyncio_app = ASyncIOApp(routes=routes)


@pytest.mark.parametrize('app', [wsgi_app, asyncio_app])
def test_session(app):
    client = TestClient(app)

    response = client.get('/')
    assert response.json() == {'username': None}

    response = client.post('/login?username=tom')
    assert response.json() == {'username': 'tom'}

    response = client.get('/')
    assert response.json() == {'username': 'tom'}

    response = client.post('/logout')
    assert response.json() == {'username': None}

    response = client.get('/')
    assert response.json() == {'username': None}

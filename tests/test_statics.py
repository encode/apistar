import os
import tempfile

from apistar.app import App
from apistar.routing import Route
from apistar.statics import serve_static
from apistar.test import TestClient


def test_static_files():
    with tempfile.TemporaryDirectory() as tempdir:
        path = os.path.join(tempdir, 'example.csv')
        with open(path, 'w') as example_file:
            example_file.write('1,2,3\n4,5,6\n')

        routes = [
            Route('/static/{path}', 'GET', serve_static)
        ]
        settings = {
            'STATICS': {
                'DIR': tempdir
            }
        }
        app = App(routes=routes, settings=settings)
        client = TestClient(app)

        response = client.get('/static/example.csv')
        assert response.status_code == 200
        assert response.text == '1,2,3\n4,5,6\n'

        response = client.head('/static/example.csv')
        assert response.status_code == 200
        assert response.text == ''

        response = client.get('/static/404')
        assert response.status_code == 404

        response = client.head('/static/404')
        assert response.status_code == 404

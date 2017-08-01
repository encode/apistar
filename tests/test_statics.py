
import os
import tempfile

from apistar import App, Route, TestClient
from apistar.handlers import serve_static
from apistar.interfaces import StaticFiles
from apistar.components.statics import WhiteNoiseStaticFiles


def test_static_files() -> None:
    with tempfile.TemporaryDirectory() as tempdir:
        path = os.path.join(tempdir, 'example.csv')
        with open(path, 'w') as example_file:
            example_file.write('1,2,3\n4,5,6\n')

        routes = [
            Route('/static/{path}', 'GET', serve_static)
        ]
        components = {
            StaticFiles: WhiteNoiseStaticFiles.configure(static_dir=tempdir)
        }

        app = App(routes=routes, components=components)
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

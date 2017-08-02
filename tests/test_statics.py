
import os
import tempfile

import pytest

from apistar import App, Route, TestClient, exceptions
from apistar.components.router import WerkzeugRouter
from apistar.components.statics import WhiteNoiseStaticFiles
from apistar.handlers import serve_static
from apistar.interfaces import Settings


def test_static_files() -> None:
    with tempfile.TemporaryDirectory() as tempdir:
        path = os.path.join(tempdir, 'example.csv')
        with open(path, 'w') as example_file:
            example_file.write('1,2,3\n4,5,6\n')

        routes = [
            Route('/static/{path}', 'GET', serve_static)
        ]
        settings = {
            'STATICS': {'ROOT_DIR': tempdir, 'PACKAGE_DIRS': ['apistar']}
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


def test_misconfigured_static_files() -> None:
    router = WerkzeugRouter([])
    settings = Settings({
        'STATICS': {'ROOT_DIR': None, 'PACKAGE_DIRS': ['apistar']}
    })
    statics = WhiteNoiseStaticFiles(router=router, settings=settings)
    with pytest.raises(exceptions.ConfigurationError):
        statics.get_url('/apistar/css/base.css')

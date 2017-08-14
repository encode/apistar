import os
import tempfile

import pytest

from apistar import Route, TestClient
from apistar.exceptions import TemplateNotFound
from apistar.frameworks.asyncio import ASyncIOApp
from apistar.frameworks.wsgi import WSGIApp
from apistar.interfaces import Templates


def get_and_render_template(username: str, templates: Templates):
    index = templates.get_template('index.html')
    return index.render(username=username)


routes = [
    Route('/get_and_render_template/', 'GET', get_and_render_template),
]


@pytest.mark.parametrize('app_class', [WSGIApp, ASyncIOApp])
def test_get_and_render_template(app_class):
    with tempfile.TemporaryDirectory() as tempdir:
        path = os.path.join(tempdir, 'index.html')
        with open(path, 'w') as index:
            index.write('<html><body>Hello, {{ username }}</body><html>')

        settings = {
            'TEMPLATES': {
                'PACKAGE_DIRS': ['apistar'],
                'ROOT_DIR': [tempdir]
            }
        }
        app = app_class(routes=routes, settings=settings)
        client = TestClient(app)
        response = client.get('/get_and_render_template/?username=tom')

        assert response.status_code == 200
        assert response.text == '<html><body>Hello, tom</body><html>'


@pytest.mark.parametrize('app_class', [WSGIApp, ASyncIOApp])
def test_template_not_found(app_class):
    settings = {
        'TEMPLATES': {
            'PACKAGE_DIRS': [],
            'ROOT_DIR': []
        }
    }
    app = app_class(routes=routes, settings=settings)
    client = TestClient(app)
    with pytest.raises(TemplateNotFound):
        client.get('/get_and_render_template/?username=tom')

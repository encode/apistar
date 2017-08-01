import os
import tempfile

import pytest

from apistar import App, Route, TestClient
from apistar.exceptions import ConfigurationError
from apistar.interfaces import Templates


def get_and_render_template(username: str, templates: Templates):
    index = templates.get_template('index.html')
    return index.render(username=username)


routes = [
    Route('/get_and_render_template/', 'GET', get_and_render_template),
]


def test_get_and_render_template():
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
        app = App(routes=routes, settings=settings)
        client = TestClient(app)
        response = client.get('/get_and_render_template/?username=tom')

        assert response.status_code == 200
        assert response.text == '<html><body>Hello, tom</body><html>'


# def test_template_not_found():
#     settings = {
#         'TEMPLATES': {
#             'PACKAGE_DIRS': [],
#             'ROOT_DIR': []
#         }
#     }
#     app = App(routes=routes, settings=settings)
#     client = TestClient(app)
#     with pytest.raises(ConfigurationError):
#         client.get('/render_template/?username=tom')

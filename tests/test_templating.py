import os
import tempfile

from apistar.app import App
from apistar.routing import Route
from apistar.settings import Settings
from apistar.templating import Template, Templates
from apistar.test import TestClient


def get_and_render_template(username: str, templates: Templates):
    index = templates.get_template('index.html')
    return index.render(username=username)


def render_template(username: str, index: Template):
    return index.render(username=username)


routes = [
    Route('/get_and_render_template/', 'GET', get_and_render_template),
    Route('/render_template/', 'GET', render_template),
]


def test_get_and_render_template():
    with tempfile.TemporaryDirectory() as tempdir:
        path = os.path.join(tempdir, 'index.html')
        with open(path, 'w') as index:
            index.write('<html><body>Hello, {{ username }}</body><html>')

        settings = Settings(
            TEMPLATES={
                'TEMPLATE_DIR': tempdir
            }
        )
        app = App(routes=routes, settings=settings)
        client = TestClient(app)
        response = client.get('/get_and_render_template/?username=tom')

        assert response.status_code == 200
        assert response.text == '<html><body>Hello, tom</body><html>'


def test_render_template():
    with tempfile.TemporaryDirectory() as tempdir:
        path = os.path.join(tempdir, 'index.html')
        with open(path, 'w') as index:
            index.write('<html><body>Hello, {{ username }}</body><html>')

        settings = Settings(
            TEMPLATES={
                'TEMPLATE_DIR': tempdir
            }
        )
        app = App(routes=routes, settings=settings)
        client = TestClient(app)
        response = client.get('/render_template/?username=tom')

        assert response.status_code == 200
        assert response.text == '<html><body>Hello, tom</body><html>'

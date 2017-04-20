import os
import tempfile

from apistar.app import App
from apistar.routing import Route
from apistar.settings import Settings
from apistar.templating import Templates
from apistar.test import TestClient


def render_template(templates: Templates):
    index = templates.get_template('index.html')
    return index.render()


routes = [
    Route('/', 'GET', render_template),
]


def test_render_template():
    with tempfile.TemporaryDirectory() as tempdir:
        path = os.path.join(tempdir, 'index.html')
        with open(path, 'w') as index:
            index.write('<html><body>Hello, world</body><html>')

        settings = Settings(
            TEMPLATES={
                'TEMPLATE_DIR': tempdir
            }
        )
        app = App(routes=routes, settings=settings)
        client = TestClient(app)
        response = client.get('/')

        assert response.status_code == 200
        assert response.text == '<html><body>Hello, world</body><html>'

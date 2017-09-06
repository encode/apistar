from apistar import Route
from apistar.frameworks.wsgi import WSGIApp as App
from apistar.handlers import serve_schema


def hello_world():
    raise NotImplementedError


routes = [
    Route('/', 'GET', hello_world),
    Route('/schema/', 'GET', serve_schema),
]
app = App(routes=routes)


def test_schema():
    ret = app.main(['schema'], standalone_mode=False)
    assert ret == (
        '{"_type":"document","_meta":{"url":"/schema/"},'
        '"hello_world":{"_type":"link","url":"/","action":"GET"}}'
    )

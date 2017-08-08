from apistar import App, Route


def hello_world():
    raise NotImplementedError


routes = [
    Route('/', 'GET', hello_world),
]
app = App(routes=routes)


def test_schema():
    ret = app.main(['schema'], standalone_mode=False)
    assert ret == b'{"_type":"document","_meta":{"url":"/"},"hello_world":{"_type":"link","action":"GET"}}'

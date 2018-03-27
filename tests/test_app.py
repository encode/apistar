from apistar import App, Route, TestClient


def view():
    return {"message": "hello"}


route = Route(url="/", method="GET", handler=view)


def after_func(response):
    return response


def on_exception(exc: Exception):
    return exc


app = App(
    routes=[route],
    run_after_handler=[after_func],
    run_on_exception=[on_exception])
client = TestClient(app)


def test_run_after_handler():
    r = client.get("/")
    assert r.json() == {"message": "hello"}


def test_run_on_error():
    r = client.get("/ZEF/")
    assert r.json() == "Not found"

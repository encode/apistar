from apistar import App, Route, TestClient
from apistar.settings import Setting, Settings


def get_settings(settings: Settings):
    return settings


def get_setting(ABC: Setting):
    return {'ABC': ABC}


routes = [
    Route('/settings/', 'GET', get_settings),
    Route('/setting/', 'GET', get_setting),
]

settings = {
    'ABC': 123,
    'XYZ': 456
}

app = App(routes=routes, settings=settings)

client = TestClient(app)


def test_settings():
    response = client.get('/settings/')
    assert response.status_code == 200
    assert response.json() == {
        'ABC': 123,
        'XYZ': 456
    }


def test_setting():
    response = client.get('/setting/')
    assert response.status_code == 200
    assert response.json() == {
        'ABC': 123,
    }


def test_use_setting_as_argument():
    abc = Setting(789)
    assert get_setting(abc) == {'ABC': 789}

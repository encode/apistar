from apistar import App, ASyncApp, TestClient

async_app = ASyncApp(routes=[])
async_test_client = TestClient(async_app)

app = App(routes=[])
test_client = TestClient(app)


def test_docs():
    response = test_client.get('/docs/')
    assert response.status_code == 200


def test_docs_async():
    response = async_test_client.get('/docs/')
    assert response.status_code == 200

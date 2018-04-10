# Testing

API Star isn't coupled to any particular testing framework.

One good option for writing your test cases is [the pytest framework][pytest].

To make it easier to run tests against your application, API Star includes
a test client, that acts as an adapter for the excellent python `requests`
library, allowing you to make requests directly to your application.

You can use the API test client with *any* WSGI or ASGI application.

```python
from apistar import test
from myproject import app


client = test.Client(app)

def test_hello_world():
    response = client.get('/hello_world/')
    assert response.status_code == 200
    assert response.json() ==  {'hello': 'world'}
```

[pytest]: https://docs.pytest.org/en/latest/

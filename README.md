# API Star ✨🚀✨🌟

A smart Web API framework, designed for Python 3.

[![Build Status](https://travis-ci.org/tomchristie/apistar.svg?branch=master)](https://travis-ci.org/tomchristie/apistar)
[![Package version](https://badge.fury.io/py/apistar.svg)](https://pypi.python.org/pypi/apistar)
[![Python versions](https://img.shields.io/pypi/pyversions/apistar.svg)](https://pypi.python.org/pypi/apistar)
[![codecov](https://codecov.io/gh/tomchristie/apistar/branch/master/graph/badge.svg)](https://codecov.io/gh/tomchristie/apistar)
---

Install API Star:

    $ pip3 install apistar

Create a new project:

    $ apistar new --template minimal
    app.py
    tests.py
    $ cat app.py
    from apistar import App, Route

    def welcome():
        return {'message': 'Welcome to API Star!'}

    app = App(routes=[
        Route('/', 'GET', welcome)
    ])

Run the application:

    $ apistar run
    Running at http://localhost:8080/

Run the tests:

    $ apistar test
    tests.py ..
    ===== 2 passed in 0.05 seconds =====

---

# Requests

API Star allows you to dynamically inject various information about the
incoming request into your views using type annotation.

```python
from apistar import http

def show_request(request: http.Request):
    return {
        'method': request.method,
        'url': request.url,
        'headers': dict(request.headers)
    }

def show_query_params(query_params: http.QueryParams):
    return {
        'params': dict(query_params)
    }

def show_user_agent(user_agent: http.Header):
    return {
        'user-agent': user_agent
    }
```

Some of the components you might use most often:

| Component     | Description |
| ------------- | ----------- |
| `Request`     | The HTTP request. Includes `.method`, `.url`, and `.headers` attributes. |
| `Headers`     | The request headers, returned as a dictionary-like object. |
| `Header`      | Lookup a single request header, corresponding to the argument name.<br/>Returns a string or `None`. |
| `QueryParams` | The request query parameters, returned as a dictionary-like object. |
| `QueryParam`  | Lookup a single query parameter, corresponding to the argument name.<br/>Returns a string or `None`. |
| `Body`        | The request body. Returns a bytestring. |

---

# Responses

By default API star expects view to return plain data, and will return
`200 OK` responses.

```python
def create_project():
    return {'name': 'new project', 'id': 123}
```

You can instead set the status code or headers by annotating the view as
returning a `Response`.

```python
def create_project() -> Response:
    data = {'name': 'new project', 'id': 123}
    headers = {'Location', 'http://example.com/project/123/'}
    return Response(data, status=201, headers=headers)
```

---

# URL Routing

Use `{curly_braces}` in your URL conf to include a URL path parameter.


```python
def echo_username(username):
    return {'message': f'Welcome, {username}!'}

app = App(routes=[
    Route('/{username}/', 'GET', echo_username)
])
```

Use type annotation on the view method to include typed URL path parameters.

```python
users = {0: 'penny', 1: 'benny', 2: 'jenny'}

def echo_username(user_id: int):
    username = users[user_id]
    return {'message': f'Welcome, {username}!'}

app = App(routes=[
    Route('/{user_id}/', 'GET', echo_username)
])
```

Parameters which do not correspond to a URL path parameter will be treated as
query parameters.

```python
def echo_username(username):
    if username is None:
        return {'message': 'Welcome!'}
    return {'message': f'Welcome, {username}!'}

app = App(routes=[
    Route('/hello/', 'GET', echo_username)
])
```

---

# WSGI

Because API views are so dynamic, they'll even let you drop right down to
returning a WSGI response directly:

```python
from apistar import wsgi

def hello_world() -> wsgi.WSGIResponse:
    wsgi.WSGIResponse(
        '200 OK',
        [('Content-Type', 'text/plain')],
        [b'Hello, world!']
    )
```

You can also inject the WSGI environment into your view arguments:

```python
def debug_environ(environ: wsgi.WSGIEnviron):
    return {
        'environ': environ
    }
```

---

# Testing

API Star includes the `py.test` testing framework. You can run all tests in
a `tests.py` module or a `tests/` directory, by using the following command:

    $ apistar test

The simplest way to test a view is to call it directly.

```python
from app import hello_world

def test_hello_world():
    assert hello_world() == {"hello": "world"}
```

There is also a test client, that allows you to make HTTP requests directly to
your application, using the `requests` library.

```python
from apistar.test import TestClient

def test_hello_world():
    client = TestClient()
    response = client.get('/hello_world/')
    assert response.status_code == 200
    assert response.json() == {"hello": "world"}
```

Requests made using the test client may use either relative URLs, or absolute
URLs. In either case, all requests will be directed at your application,
rather than making external requests.

```python
response = client.get('http://www.example.com/hello_world/')
```

---

# Components

You can create new components to inject into your views, by declaring a
class with a `build` method. For instance:

```python
import base64

class Username(str):
    """
    A component which returns the username that the incoming request
    is associated with, using HTTP Basic Authentication.
    """
    @classmethod
    def build(cls, authorization: http.Header):
        if authorization is None:
            return None
        scheme, token = authorization.split()
        if scheme.lower() != 'basic':
            return None
        username, password = base64.b64decode(token).decode('utf-8').split(':')
        return cls(username)
```

You can then use your component in a view:

```python
def say_hello(username: Username):
    return {'hello': username}
```

A complete listing of the available built-in components:

Component             | Description
----------------------|-------------
`app.App`             | The application instance.
`http.Method`         | The HTTP method of the request, such as `GET`.
`http.Host`           | The host component of the request URL, such as `'example.com'`.
`http.Port`           | The port number that the request is made to, such as 443.
`http.Scheme`         | The scheme component of the request URL, such as 'https'.
`http.Path`           | The path component of the request URL, such as `/api/v1/my_view/`.
`http.QueryString`    | The query component of the request URL, such as `page=2`.
`http.URL`            | The full URL of the request, such as `https://example.com/api/v1/my_view/?page=2`.
`http.Body`           | The body of the request, as a bytestring.
`http.QueryParams`    | A multi-dict containing the request query parameters.
`http.QueryParam`     | A single request query parameter, corresponding to the keyword argument name. Automatically used for data arguments.
`http.Headers`        | A multi-dict containing the request headers parameters.
`http.Header`         | A single request query parameter, corresponding to the keyword argument name.
`http.Request`        | The full request instance.
`http.Response`       | A return type for returning an HTTP response explicitly.
`http.ResponseData`   | A return type for plain data responses.
`wsgi.Environ`        | The WSGI environ of the incoming request.
`wsgi.Response`       | A return type for directly returning a WSGI response.
`routing.URLPathArgs` | A dictionary containing all the matched URL path arguments.
`routing.URLPathArg`  | A single URL path argument, corresponding to the keyword argument name. Automatically used for data arguments with a matching URL path component.
`pipelines.ArgName`   | The keyword argument with which a component is being injected.

---

# Performance

The following results were obtained on a 2013 MacBook Air, using the simplest
"JSON Serialization" [TechEmpower benchmark](https://www.techempower.com/benchmarks/).

Framework | Configuration       | Requests/sec | Avg Latency
----------|---------------------|--------------|-------------
API Star  | gunicorn + meinheld | 25,195       |  7.94ms
Sanic     | uvloop              | 21,233       | 10.19ms
Falcon    | gunicorn + meinheld | 16,692       | 12.08ms
Flask     | gunicorn + meinheld |  5,238       | 38.28ms

A pull request [has been issued](https://github.com/TechEmpower/FrameworkBenchmarks/pull/2633)
to add API Star to future rounds of the TechEmpower benchmarks. In the future we
plan to be adding more realistic & useful test types, such as database query performance.

---

# Deployment

A development server is available, using the `run` command:

    $ apistar run

The recommended production deployment is GUnicorn, using the Meinheld worker.

    $ pip install gunicorn
    $ pip install meinheld
    $ gunicorn app:app.wsgi --workers=4 --bind=0.0.0.0:5000 --pid=pid --worker-class=meinheld.gmeinheld.MeinheldWorker

Typically you'll want to run as many workers as you have CPU cores on the server.

---

# Development

To work on the API Star codebase, you'll want to clone the repository,
and create a Python virtualenv with the project requirements installed:

    $ git clone git@github.com:tomchristie/apistar.git
    $ cd apistar
    $ ./scripts/setup

To run the tests and code linting:

    $ ./scripts/test
    $ ./scripts/lint

---

<p align="center"><i>API Star is <a href="https://github.com/tomchristie/apistar/blob/master/LICENSE.md">BSD licensed</a> code.<br/>Designed & built in Brighton, England.</i><br/>&mdash; ⭐️ &mdash;</p>

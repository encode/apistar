# API Star ✨🚀✨🌟

A smart Web API framework, designed for Python 3.

[![Build Status](https://travis-ci.org/tomchristie/apistar.svg?branch=master)](https://travis-ci.org/tomchristie/apistar)
[![codecov](https://codecov.io/gh/tomchristie/apistar/branch/master/graph/badge.svg)](https://codecov.io/gh/tomchristie/apistar)
[![Package version](https://badge.fury.io/py/apistar.svg)](https://pypi.python.org/pypi/apistar)
[![Python versions](https://img.shields.io/pypi/pyversions/apistar.svg)](https://www.python.org/doc/versions/)

**Community:** http://discuss.apistar.org/ 🤔 💭 🤓 💬 😎

---

Install API Star:

    $ pip3 install apistar

Create a new project:

    $ apistar new . --layout minimal
    app.py
    tests.py
    $ cat app.py
    from apistar import App, Route

    def welcome():
        return {'message': 'Welcome to API Star!'}


    routes = [
        Route('/', 'GET', welcome)
    ]

    app = App(routes=routes)


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

# Templates

API Star includes a templating component, that allows you to return templated
responses, using Jinja2.

**templates/index.html:**

```html
<html>
    <body>
        <h1>Hello, {{ username }}</h1>
    </body>
</html>
```

**app.py:**

```python
from apistar import App, Route, Templates
import os

ROOT_DIR = os.path.dirname(__file__)

def hello(username: str, templates: Templates):
    index = templates.get_template('index.html')
    return index.render(username=username)

routes = [
    Route('/', 'GET', hello)
]

settings = {
    'TEMPLATES': {
        'DIRS': [os.path.join(ROOT_DIR, 'templates')]
    }
}

app = App(routes=routes, settings=settings)
```

You can also use the `Template` component to inject a single template instance
as a view argument:

```python
def hello(username: str, index: Template):
    return index.render(username=username)
```

This will default to attempting to locate `index.html`, based on the argument
name of `index`.

Returning a string response from a view will default to using the `text/html`
content type. You can override this by returning a `Response`, including an
explicit `Content-Type` header.

---

# Settings

Application settings are configured at the point of instantiating the app.


```python
routes = [...]

settings = {
    'TEMPLATES': {
        'TEMPLATE_DIR': '/foo/bar'
    }
}

app = App(routes=routes, settings=settings)
```

You can include the application settings in a view, by using the `Settings`
type annotation:

```python
from apistar.settings import Settings


def debug_settings(settings: Settings):
    """
    Return a JSON response containing the application settings dictionary.
    """
    return settings
```

Similarly you can include a single application setting:

```python
def debug_template_settings(TEMPLATES: Setting):
    """
    Return a JSON response containing the application settings dictionary.
    """
    return {'TEMPLATES': TEMPLATES}
```

More typically you'll want to include settings into the `build` method of
custom components, so that you can control their initialization, based on the
application settings.

---

# SQLAlchemy Backend

APIstar has support for SQLAlchemy. To use this you first need to install `sqlalchemy` and your chosen DBAPI (e.g. `psycopg2` for PostgreSQL).


```bash
$ pip install sqlalchemy
$ pip install psycopg2
```

**Settings**

You then need to add the database config to your settings passing in an SQLAlchemy [`Metadata`](http://docs.sqlalchemy.org/en/latest/core/metadata.html) instance into the config.

```python
    from sqlalchemy.ext.declarative import declarative_base

    Base = declarative_base()

    class Kitten(Base):
        __tablename__ = "Kitten"
        id = Column(Integer, primary_key=True)
        name = Column(String)

    # in app.py

    routes = [...]

    settings = {
        "DATABASE": {
            "URL": "postgresql://:@localhost/apistar",
            "METADATA": Base.metadata
        }
    }

    app = App(routes=routes, settings=settings)
)
```

*Note: You do not have to use `declarative_base` and can instead use the standard `MetaData` class if you prefer.*


**Creating the database tables**

Before starting you app you will likely need to create the database tables declared in your MetaData which you can do with the following command:

```bash
$ apistar create_tables
```


**Accessing the database**

To access the database in your view, use the `Database` has the following attributes:

- `engine` - The global [`Engine`](http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine) instance.
- `metadata` - The [`MetaData`](http://docs.sqlalchemy.org/en/latest/core/metadata.html#sqlalchemy.schema.MetaData) object passed into the settings.
- `session_class` - A bound [`sessionmaker`](http://docs.sqlalchemy.org/en/latest/orm/session_api.html#session-and-sessionmaker) factory.

```python
from apistar.backends import SQLAlchemy

def create_kitten(db: SQLAlchemy):
    session = db.session_class()
    add_kitten = Kitten(name='Grumpy Cat')
    session.add(add_kitten)
    session.commit()
```


---

# Testing

API Star includes the `py.test` testing framework. You can run all tests in
a `tests.py` module or a `tests/` directory, by using the following command:

```bash
$ apistar test
```

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

Component              | Description
-----------------------|-------------
`app.App`              | The application instance.
`http.Method`          | The HTTP method of the request, such as `GET`.
`http.Host`            | The host component of the request URL, such as `'example.com'`.
`http.Port`            | The port number that the request is made to, such as 443.
`http.Scheme`          | The scheme component of the request URL, such as 'https'.
`http.Path`            | The path component of the request URL, such as `/api/v1/my_view/`.
`http.QueryString`     | The query component of the request URL, such as `page=2`.
`http.URL`             | The full URL of the request, such as `https://example.com/api/v1/my_view/?page=2`.
`http.Body`            | The body of the request, as a bytestring.
`http.QueryParams`     | A multi-dict containing the request query parameters.
`http.QueryParam`      | A single request query parameter, corresponding to the keyword argument name. Automatically used for data arguments.
`http.Headers`         | A multi-dict containing the request headers parameters.
`http.Header`          | A single request query parameter, corresponding to the keyword argument name.
`http.Request`         | The full request instance.
`http.Response`        | A return type for returning an HTTP response explicitly.
`http.ResponseData`    | A return type for plain data responses.
`pipelines.ArgName`    | The keyword argument with which a component is being injected into the view. May be used within component `build` methods.
`routing.URLPathArgs`  | A dictionary containing all the matched URL path arguments.
`routing.URLPathArg`   | A single URL path argument, corresponding to the keyword argument name. Automatically used for data arguments with a matching URL path component.
`settings.Settings`    | A dictionary containing the application settings.
`settings.Setting`     | A single named setting, as determined by the argument name.
`templating.Templates` | The template environment.
`templating.Template`  | A single loaded template, as determined by the argument name.
`wsgi.WSGIEnviron`     | The WSGI environ of the incoming request.
`wsgi.WSGIResponse`    | A return type for directly returning a WSGI response.

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

## "Serverless" deployments

API Star can also be deployed on so called "serverless" platforms.
A good option for using API Star with this style of deployment is [Zappa](https://github.com/Miserlou/Zappa), which allows you to deploy
any Python WSGI server onto AWS Lambda.

In order to use `zappa`, you'll need to expose the app.wsgi property
to the top level of the `app.py` module.

```python
app = App(...)

wsgi_app = app.wsgi
```

You should then follow [Zappa's installation instructions](https://github.com/Miserlou/Zappa#installation-and-configuration).

Your `zappa_settings.json` configuration file should look something like this:

```
{
    "dev": {
        "app_function": "app.wsgi_app",
        "aws_region": "us-east-1",
        "profile_name": "default",
        "s3_bucket": "<a-unique-s3-bucket-name>",
    }
}
```

---

# Development

To work on the API Star codebase, you'll want to clone the repository,
and create a Python virtualenv with the project requirements installed:

    $ git clone git@github.com:tomchristie/apistar.git
    $ cd apistar
    $ ./scripts/setup

To run the continuous integration tests and code linting:

    $ ./scripts/test
    $ ./scripts/lint

---

<p align="center"><i>API Star is <a href="https://github.com/tomchristie/apistar/blob/master/LICENSE.md">BSD licensed</a> code.<br/>Designed & built in Brighton, England.</i><br/>&mdash; ⭐️ &mdash;</p>

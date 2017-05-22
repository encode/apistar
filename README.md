# API Star ✨🚀✨🌟

A smart Web API framework, designed for Python 3.

[![Build Status](https://travis-ci.org/tomchristie/apistar.svg?branch=master)](https://travis-ci.org/tomchristie/apistar)
[![codecov](https://codecov.io/gh/tomchristie/apistar/branch/master/graph/badge.svg)](https://codecov.io/gh/tomchristie/apistar)
[![Package version](https://badge.fury.io/py/apistar.svg)](https://pypi.python.org/pypi/apistar)
[![Python versions](https://img.shields.io/pypi/pyversions/apistar.svg)](https://www.python.org/doc/versions/)

**Community:** https://discuss.apistar.org/ 🤔 💭 🤓 💬 😎

![screenshot](docs/img/apistar.gif)

---

# Features

Why should you consider using API Star for your next Web API project?

* **API documentation** - Interactive API documentation, that's guaranteed to always
be in sync with your codebase.
* **Client libraries** - JavaScript and Python client libraries, driven by the schemas that API Star generates.
* **Schema generation** - Support for generating Swagger or RAML API schemas.
* **Expressive** - Type annotated views, that make for expressive, testable code.
* **Performance** - Dynamic behavior for determining how to run each view makes API Star incredibly efficient.

---

# Table of Contents

- [Quickstart](#quickstart)
- [HTTP](#http)
    - [Requests](#requests)
    - [Responses](#responses)
    - [URL Routing](#url-routing)
- [Schemas](#schemas)
    - [Data Validation](#data-validation)
    - [Serialization](#serialization)
    - [Generating API Schemas](#generating-api-schemas)
- [Building Websites](#building-websites)
    - [Templates](#templates)
    - [Static Files](#static-files)
- [Settings & Environment](#settings--environment)
    - [Application settings](#application-settings)
    - [Environment](#environment)
- [ORM](#orm)
  - [SQLAlchemy](#sqlalchemy)
  - [Django](#django)
- [Testing](#testing)
- [Components](#components)
- [WSGI](#wsgi)
- [Performance](#performance)
- [Deployment](#deployment)
    - [The Development Server](#the-development-server)
    - [Running in Production](#running-in-production)
    - ["Serverless" Deployments](#serverless-deployments)
- [Development](#development)

---

# Quickstart

Install API Star:

    $ pip3 install apistar

Create a new project:

    $ apistar new . --layout minimal
    app.py
    tests.py
    $ cat app.py
    from apistar import App, Include, Route
    from apistar.docs import docs_routes
    from apistar.statics import static_routes


    def welcome(name=None):
        if name is None:
            return {'message': 'Welcome to API Star!'}
        return {'message': 'Welcome to API Star, %s!' % name}


    routes = [
        Route('/', 'GET', welcome),
        Include('/docs', docs_routes),
        Include('/static', static_routes)
    ]

    app = App(routes=routes)


Run the application:

    $ apistar run
    Running at http://localhost:8080/

Run the tests:

    $ apistar test
    tests.py ..
    ===== 2 passed in 0.05 seconds =====

View the interactive API documentation:

    $ open http://localhost:8080/docs/

![screenshot](docs/img/apistar.png)

---

# HTTP

## Requests

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

## Responses

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

## URL Routing

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
query parameters for `GET` and `DELETE` requests, or part of the request body
for `POST`, `PUT`, and `PATCH` requests.

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

# Schemas

API Star comes with a type system that allows you to express constraints on the
expected inputs and outputs of your interface.

Here’s a quick example of what the schema type system in API Star looks like:

```python
class Rating(schema.Integer):
    minimum = 1
    maximum = 5


class ProductSize(schema.Enum):
    enum = ['small', 'medium', 'large']


class Product(schema.Object):
    properties = {
        'name': schema.String(max_length=100),
        'rating': schema.Integer(minimum=1, maximum=5),
        'in_stock': schema.Boolean,
        'size': ProductSize,
    }
```

## Data Validation

The main benefit of expressing our data constraints in a type system is that we
can then use those types as annotations on our handler functions.

```python
def create_product(product: Product):
    ...

routes = [
    Route('/create_product/', 'POST', create_product)
]
```

## Serialization

In addition to using the schema types for input validation, you can also use
them to serialize the return values of your handler functions.

```python
def list_products() -> List[Product]
    ...
    return [Product(...) for record in records]
```

## API Reference

The following schema types are currently supported:

### String

Validates string data. A subclass of `str`.

* `default` - A default to be used if a field using this schema is missing from a parent `Object`.
* `max_length` - A maximum valid length for the data.
* `min_length` - A minimum valid length for the data.
* `pattern` - A string or compiled regex that the data must match.
* `format` - An identifier indicating a complex datatype with a string representation. For example `"date"`, to represent an ISO 8601 formatted date string.
* `trim_whitespace` - `True ` if leading and trailing whitespace should be stripped from the data. Defaults to `True`.

### Number

Validates numeric data. A subclass of `float`.

* `default` - A default to be used if a field using this schema is missing from a parent `Object`.
* `maximum` - A float representing the maximum valid value for the data.
* `minimum` - A float representing the minimum valid value for the data.
* `exclusive_maximum` - `True` for an exclusive maximum limit. Defaults to `False`.
* `exclusive_minimum` - `True` for an exclusive minimum limit. Defaults to `False`.
* `multiple_of` - A float that the data must be strictly divisible by, in order to be valid.

### Integer

Validates integer data. A subclass of `int`.

* `default` - A default to be used if a field using this schema is missing from a parent `Object`.
* `maximum` - An int representing the maximum valid value for the data.
* `minimum` - An int representing the minimum valid value for the data.
* `exclusive_maximum` - `True` for an exclusive maximum limit. Defaults to `False`.
* `exclusive_minimum` - `True` for an exclusive minimum limit. Defaults to `False`.
* `multiple_of` - An integer that the data must be strictly divisible by, in order to be valid.

### Boolean

Validates boolean input. Returns either `True` or `False`.

* `default` - A default to be used if a field using this schema is missing from a parent `Object`.

### Enum

Validates string input, against a list of valid choices. A subclass of `str`.

* `default` - A default to be used if a field using this schema is missing from a parent `Object`.
* `enum` - A list of valid string values for the data.

### Object

Validates dictionary or object input. A subclass of `dict`.

* `default` - A default to be used if a field using this schema is missing from a parent `Object`.
* `properties` - A dictionary mapping string key names to schema or type values.

Note that child properties are considered to be required if they do not have a `default` value.

## Generating API Schemas

API Star is designed to be able to map well onto API description formats, known as "API Schemas".

There is currently *provisional* support for writing Swagger, RAML, or CoreJSON schemas.
See [#69](https://github.com/tomchristie/apistar/issues/69) for more details on work still to be done here.

The default output format is the built-in CoreJSON support:

```shell
$ apistar schema
{"_type":"document", ...}
```

The OpenAPI (Swagger) and RAML codecs are optional, and require installation of additional packages:

#### Swagger

```shell
$ pip install openapi-codec
$ apistar schema --format openapi
{"swagger": "2.0", "info": ...}
```

#### RAML

```shell
$ pip install raml-codec
$ apistar schema --format raml
#%RAML 0.8
...
```

---

# Building Websites

Although API Star is designed primarily with Web APIs in mind, it is a
general purpose framework, and does also give you the tools you need
to build regular websites.

## Templates

API Star includes a templating component, that allows you to return templated
responses, using [Jinja2](http://jinja.pocoo.org/).

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

def hello(username: str, templates: Templates):
    index = templates.get_template('index.html')
    return index.render(username=username)

routes = [
    Route('/', 'GET', hello)
]

settings = {
    'TEMPLATES': {
        'DIRS': ['templates']
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

## Static Files

For serving static files, API Star uses [whitenoise](http://whitenoise.evans.io/en/stable/).

First make sure to install the `whitenoise` package.

```
$ pip install whitenoise
```

Next, you'll then need to include the `serve_static` handler in your routes.
This function expects to take a single URL argument, named `path`.

```python
from apistar.routing import Route
from apistar.statics import serve_static

routes = [
    # ...
    Route('/static/{path}', 'GET', serve_static)
]
```

Finally, include the directory that you'd like to serve static files from
in your settings, like so:

```python
settings = {
    'STATICS': {
        'DIR': 'statics'
    }
}

app = App(routes=routes, settings=settings)
```

---

# Settings & Environment

## Application settings

Application settings are configured at the point of instantiating the app.


```python
routes = [
    # ...
]

settings = {
    'TEMPLATES': {
        'DIRS': ['templates']
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

## Environment

Typically you'll want to follow the "twelve-factor app" pattern and [store
configuration variables in the environment](https://12factor.net/config), rather
than keeping them under source control.

API Star provides an `Environment` class that allows you to load the environment,
and ensure that it is correctly configured.

```python
from apistar import environment, schema


class Env(environment.Environment):
    properties = {
        'DEBUG': schema.Boolean(default=False),
        'DATABASE_URL': schema.String(default='sqlite://')
    }

env = Env()
```

Once you have an `Environment` instance, you can use it when creating
the application settings.


```python
settings = {
    'DATABASE': {
        'URL': env['DATABASE_URL']
    }
}
```

---

# ORM

## SQLAlchemy

API Star has optional support for [SQLAlchemy](https://www.sqlalchemy.org/).
To use this you first need to install `sqlalchemy` and your chosen [database driver](http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls).


```bash
$ pip install sqlalchemy
$ pip install psycopg2
```

**Settings**

You then need to add the database config to your settings:

* `URL` - The [Database URL](http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls).
* `METADATA` - The SQLAlchemy [`Metadata`](http://docs.sqlalchemy.org/en/latest/core/metadata.html) instance, typically from the `declarative_base`.

```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class Customer(Base):
    __tablename__ = "Customer"
    id = Column(Integer, primary_key=True)
    name = Column(String)

routes = [
    # ...
]

settings = {
    "DATABASE": {
        "URL": "postgresql://:@localhost/apistar",
        "METADATA": Base.metadata
    }
}

app = App(routes=routes, settings=settings)
```

A few common configurations are listed below.

Database   | Driver                      | URL format
---------- | --------------------------- | ----------------
PostgreSQL | `psycopg2`                  | `postgresql://<username>:<password>@localhost/example`
MySQL      | `mysql-python`              | `mysql://<username>:<password>@localhost/example`
SQLite     | `sqlite3` (Python built-in) | `sqlite:///example.db`

**Creating the database tables**

Before starting you app you will likely need to create the database tables declared in your MetaData which you can do with the following command:

```bash
$ apistar create_tables
```

**Accessing the database**

To access the database in your view, include the `SQLAlchemy` component.
This has the following attributes:

- `engine` - The global [`Engine`](http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine) instance.
- `metadata` - The [`MetaData`](http://docs.sqlalchemy.org/en/latest/core/metadata.html#sqlalchemy.schema.MetaData) object passed into the settings.
- `session_class` - A bound [`sessionmaker`](http://docs.sqlalchemy.org/en/latest/orm/session_api.html#session-and-sessionmaker) factory.

```python
from apistar.backends import SQLAlchemy

def create_customer(db: SQLAlchemy, name: str):
    session = db.session_class()
    customer = Customer(name=name)
    session.add(customer)
    session.commit()
    return {'name': name}
```

## Django

API Star has optional support for [Django ORM](https://docs.djangoproject.com/en/1.11/topics/db/).
To use this you first need to install `django` and your chosen [database driver](https://docs.djangoproject.com/en/1.11/ref/databases/).


```bash
$ pip install django
```

**Settings**

You then need to add the database config to your settings:

```python
from apistar import App
from project.routes import routes


settings = {
    'DATABASES': {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'apidjango',
            'HOST': 'localhost',
            'USER': 'nirgalon',
            'PASSWORD': ''
        }
    },
    'INSTALLED_APPS': ('project',)
}


app = App(routes=routes, settings=settings)
```

**Migrations**

You also need to manually create the `migrations` directory inside the `project` directory.

Before starting you app you will likely need to make migrations and then migrate which you can do with the following commands:

```bash
$ apistar makemigrations
$ apistar migrate
```

**Create a new model**

To create a new Django model you will want to create a new `models.py` file and declare it.

```python
from django.db import models

class Star(models.Model):
    name = models.CharField(max_length=255)
    age = models.IntegerField()
```

**Accessing the database**

To access the database in your view, include the `Django` component.
This has the following attributes:

```python
from apistar.backends import DjangoBackend

def create_star(orm: DjangoBackend, star: schemas.Star):
    """Create a new star object"""
    star = orm.Star(**star)
    star.save()
    return {'star': {'name': star.name, 'id': star.id}}

def list_stars(orm: DjangoBackend):
    """Get all the stars objects"""
    Star = orm.Star
    return {'stars': list(Star.objects.values('name', 'id'))}
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

API Star dynamically determines exactly what does and does not need to
run for any given view, based on the annotations it includes. This means that
it can be incredibly efficient.

For a simple JSON serialization test case, the [TechEmpower benchmarks][techempower]
rank API Star as achieving the highest throughput of any Python, JavaScript, Ruby,
or Go framework.

![Benchmarks](docs/img/benchmarks.png)

We're also able to replicate similar results locally. The following results
were obtained on a 2013 MacBook Air, against the same JSON serialization test case.

Framework | Configuration       | Requests/sec | Avg Latency
----------|---------------------|--------------|-------------
API Star  | gunicorn + meinheld | 25,195       |  7.94ms
Sanic     | uvloop              | 21,233       | 10.19ms
Falcon    | gunicorn + meinheld | 16,692       | 12.08ms
Flask     | gunicorn + meinheld |  5,238       | 38.28ms

API Star optionally supports the `ujson` package for improvements in serialization performance. Currently `ujson` will automatically be used if the package is installed.

**Proviso**:

It's worth noting that other types of test case would give different results.
In particular, API Star would likely lose out to asynchronous frameworks once
database access or other blocking operations are included in the test case.

We'll be working towards adding further test case types to the TechEmpower
benchmarks in the coming weeks, and are also planning to add support for an
asynchronous deployment mode.

Its also important to recognize that raw latency or throughput numbers are
typically not the most important factor to take into consideration when choosing
a framework. Having said that, our aim is for API Star to hit the sweet spot for
both performance and for productivity.

---

# Deployment

## The Development Server

A development server is available, using the `run` command:

    $ apistar run

## Running in Production

The recommended production deployment is Gunicorn, using the Meinheld worker.

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

[techempower]: https://www.techempower.com/benchmarks/#section=data-r14&hw=ph&test=json

# API Star ✨🚀✨🌟

A smart Web API framework, designed for Python 3.

[![Build Status](https://travis-ci.org/encode/apistar.svg?branch=master)](https://travis-ci.org/encode/apistar)
[![codecov](https://codecov.io/gh/encode/apistar/branch/master/graph/badge.svg)](https://codecov.io/gh/encode/apistar)
[![Package version](https://badge.fury.io/py/apistar.svg)](https://pypi.python.org/pypi/apistar)
[![Python versions](https://img.shields.io/pypi/pyversions/apistar.svg)](https://www.python.org/doc/versions/)

**Community:** https://discuss.apistar.org/ 🤔 💭 🤓 💬 😎

![screenshot](docs/img/apistar.gif)

---

# Features

Why should you consider using API Star for your next Web API project?

* **API documentation** - Interactive API documentation, that's guaranteed to always
be in sync with your codebase.
* **Client libraries** - JavaScript and Python client libraries, driven by the typesystems that API Star generates.
* **Schema generation** - Support for generating Swagger or RAML API typesystems.
* **Expressive** - Type annotated views, that make for expressive, testable code.
* **Performance** - Dynamic behaviour for determining how to run each view makes API Star incredibly efficient.
* **Throughput** - Support for asyncio to allow for building high-throughput non-blocking applications.

---

# Table of Contents

- [Quickstart](#quickstart)
- [Apps](#apps)
    - [Sync or ASync](#sync-or-async)
    - [App configuration](#app-configuration)
- [HTTP](#http)
    - [Requests](#requests)
    - [Responses](#responses)
    - [Using annotations](#using-annotations)
- [URL Routing](#url-routing)
    - [Routing basics](#routing-basics)
    - [Building URLs](#building-urls)
    - [Managing larger projects](#managing-larger-projects)
- [Template and Static files](#templates-and-static-files)
    - [Templates](#templates)
    - [Static Files](#static-files)
- [Type System](#type-system)
    - [Data validation](#data-validation)
    - [Serialization](#serialization)
- [Testing](#testing)
    - [The Test Client](#the-test-client)
- [API Schemas](#api-schemas)
    - [Serving an API Schema](#serving-an-api-schema)
    - [Key concepts](#key-concepts)
- [Client Library](#client-library)
    - [Using the client library](#using-the-client-library)
    - [Advanced usage](#advanced-usage)
- [Event Hooks](#event-hooks)
    - [Using event hooks](#using-event-hooks)
- [Components](#components)
    - [Component reference](#component-reference)
    - [Using custom components](#using-custom-components)
- [Deployment](#deployment)
    - [The development server](#the-development-server)
    - [Running in production](#running-in-production)

---

# Quickstart

Install API Star:

```bash
$ pip3 install apistar
```

Create a new project in `app.py`:

```python
from apistar import App, Route


def welcome(name=None):
    if name is None:
        return {'message': 'Welcome to API Star!'}
    return {'message': 'Welcome to API Star, %s!' % name}


routes = [
    Route('/', method='GET', handler=welcome),
]

app = App(routes=routes)


if __name__ == '__main__':
    app.serve('127.0.0.1', 5000, use_debugger=True, use_reloader=True)
```

---

# Sync or ASync

API Star supports both multi-threaded (WSGI) and asyncio (ASGI) modes of operation.

The Python ecosystem currently has far more support for multi-threaded concurrency.
Most existing database adapters, ORMs, and other networking components are
designed to work within this context. If you're not sure which of the two modes
you want, then you probably want to use the standard `App` instance.

For web services where you need particularly high throughput-per-instance
you might want to choose the asyncio mode. If you do so then you'll need to
make sure that you're only ever making network requests or disk access using
async operations, and packages designed to work with asyncio.

For an asyncio-based application, you should use the `ASyncApp` class.

```python
from apistar import ASyncApp

...

app = ASyncApp(routes=routes)
```

---

# HTTP

## Requests

To access the incoming HTTP request, use the `http.Request` class as an
annotation on the handler function.

```python
from apistar import http


def echo_request_info(request: http.Request) -> dict:
    return {
        'method': request.method,
        'url': request.url,
        'headers': dict(request.headers),
        'body': request.body.decode('utf-8')
    }
```

API Star allows you to dynamically inject various other information about the
incoming request into your views using type annotation.

```python
from apistar import http


def echo_query_params(query_params: http.QueryParams) -> dict:
    return {
        'params': dict(query_params)
    }

def echo_user_agent(user_agent: http.Header) -> dict:
    return {
        'user-agent': user_agent
    }
```

Some of the components you might use most often:

| Component          | Description |
| ------------------ | ----------- |
| `http.Request`     | The HTTP request. Includes `.method`, `.url`, and `.headers` attributes. |
| `http.Headers`     | The request headers, returned as a dictionary-like object. |
| `http.Header`      | Lookup a single request header, corresponding to the argument name.<br/>Returns a string or `None`. |
| `http.QueryParams` | The request query parameters, returned as a dictionary-like object. |
| `http.QueryParam`  | Lookup a single query parameter, corresponding to the argument name.<br/>Returns a string or `None`. |
| `http.Body`        | The request body. Returns a bytestring. |

## Responses

By default API star uses HTML responses for handlers that return strings,
and JSON responses for anything else.

```python
def hello_world() -> dict:
    return {'text': 'Hello, world!'}
```

For more control over the response use the `JSONResponse` and
`HTMLResponse` classes.

```python
from apistar import http


def hello_world(accept_language: http.Header) -> http.JSONResponse:
    if 'de' in accept_language:
        data = {'text': 'Hallo, Welt!'}
    else:
        data = {'text': 'Hello, world!'}
    headers = {'Vary': 'Accept-Language'}
    return http.JSONResponse(data, status_code=200, headers=headers)
```

For other content types, use a `Response` class, and set the content-type
header explicitly.

```python
from apistar import http


def hello_world() -> http.Response:
    content = 'Hello, world!'
    headers = {'Content-Type': 'text/plain'}
    return http.Response(content, headers=headers)
```

---

## URL Routing

Use `{curly_braces}` in your URL conf to include a URL path parameter.

```python
from apistar import App, Route


def echo_username(username):
    return {'message': 'Welcome, %s!' % username}


app = App(routes=[
    Route('/users/{username}/', 'GET', echo_username)
])
```

Use type annotation on a handler to match integers or floats in the URL string.

```python
from apistar import App, Route, exceptions


USERS = {1: 'hazel', 2: 'james', 3: 'ana'}

def echo_username(user_id: int):
    if user_id not in USERS:
        raise exceptions.NotFound()
    return {'message': 'Welcome, %s!' % USERS[user_id]}

routes = [
    Route('/users/{user_id}/', method='GET', handler=echo_username)
]

app = App(routes=routes)
```

If you want to capture a complete URL path parameter *including any `/`
characters* then use `{+curly_braces}`.

```
app = App(routes=[
    Route('/static/{+path}', method='GET', handler=serve_file)
])
```

### Building URLS

You can generate URL strings that match your routing configuration by using `app.build_url(name, **parameters)`.

```python
from apistar import App, Route, exceptions


USERS = {1: 'hazel', 2: 'james', 3: 'ana'}

def list_users(user_id: int, app: App):
    return [
        {
            'username': username,
            'url': app.build_url('get_user', user_id=user_id)
        } for user_id, username in USERS.items()
    ]

def get_user(user_id: int, app: App):
    if user_id not in USERS:
        raise exceptions.NotFound()
    return {
        'username': USERS[user_id],
        'url': app.build_url('get_user', user_id=user_id)
    }

routes = [
    Route('/users/', method='GET', handler=list_users),
    Route('/users/{user_id}/', method='GET', handler=get_user)
]

app = App(routes=routes)
```

### Routing in larger projects

In many projects you may want to split your routing into different sections.
Use `Include` to add a list of routes under a single URL prefix.

**myproject/users.py**

```python
from apistar import Route, exceptions


USERS = {1: 'hazel', 2: 'james', 3: 'ana'}

def list_users(user_id: int, app: App):
    return [
        {
            'username': username,
            'url': app.build_url('users:get_user', user_id=user_id)
        } for user_id, username in USERS.items()
    ]

def get_user(user_id: int, app: App):
    if user_id not in USERS:
        raise exceptions.NotFound()
    return {
        'username': USERS[user_id],
        'url': app.build_url('users:get_user', user_id=user_id)
    }

routes = [
    Route('/', method='GET', handler=list_users),
    Route('/{user_id}', method='GET', handler=get_user),
]
```

**app.py:**

```python
from apistar import
from myproject import users

routes = [
    Include('/users', name='users', routes=users.routes),
    ...
]

app = App(routes=routes)
```

---

# Type System

API Star comes with a type system that allows you to express constraints on the
expected inputs and outputs of your interface.

Here’s a quick example of what the type system in API Star looks like:

```python
from apistar import types, fields


class Product(types.Type):
    name = fields.String(max_length=100)
    rating = fields.Integer(minimum=1, maximum=5)
    in_stock = fields.Boolean()
    size = fields.String(enum=['small', 'medium', 'large'])
```

You can use the type system both for validation of incoming request data, and
for serializing outgoing response data.

## Validation

```python
def create_product(product: Product):
    ...

routes = [
    Route('/create_product/', method='POST', handler=create_product)
]
```

## Serialization

...

```python
import typing


def list_products() -> typing.List[Product]:
    queryset = ...  # Query returning products from a data store.
    return [Product(record) for record in queryset]
```

## API Reference

The following typesystem types are supported:

### String

Validates string data. A subclass of `str`.

* `default` - A default to be used if a field using this typesystem is missing from a parent `Object`.
* `max_length` - A maximum valid length for the data.
* `min_length` - A minimum valid length for the data.
* `pattern` - A string or compiled regex that the data must match.
* `format` - An identifier indicating a complex datatype with a string representation. For example `"date"`, to represent an ISO 8601 formatted date string.
* `trim_whitespace` - `True ` if leading and trailing whitespace should be stripped from the data. Defaults to `True`.
* `description` - A description for online documentation

### Number

Validates numeric data. A subclass of `float`.

* `default` - A default to be used if a field using this typesystem is missing from a parent `Object`.
* `maximum` - A float representing the maximum valid value for the data.
* `minimum` - A float representing the minimum valid value for the data.
* `exclusive_maximum` - `True` for an exclusive maximum limit. Defaults to `False`.
* `exclusive_minimum` - `True` for an exclusive minimum limit. Defaults to `False`.
* `multiple_of` - A float that the data must be strictly divisible by, in order to be valid.
* `description` - A description for online documentation

### Integer

Validates integer data. A subclass of `int`.

* `default` - A default to be used if a field using this typesystem is missing from a parent `Object`.
* `maximum` - An int representing the maximum valid value for the data.
* `minimum` - An int representing the minimum valid value for the data.
* `exclusive_maximum` - `True` for an exclusive maximum limit. Defaults to `False`.
* `exclusive_minimum` - `True` for an exclusive minimum limit. Defaults to `False`.
* `multiple_of` - An integer that the data must be strictly divisible by, in order to be valid.
* `description` - A description for online documentation

### Boolean

Validates boolean input. Returns either `True` or `False`.

* `default` - A default to be used if a field using this typesystem is missing from a parent `Object`.
* `description` - A description for online documentation

### Enum

Validates string input, against a list of valid choices. A subclass of `str`.

* `default` - A default to be used if a field using this typesystem is missing from a parent `Object`.
* `enum` - A list of valid string values for the data.
* `description` - A description for online documentation

### Object

Validates dictionary or object input. A subclass of `dict`.

* `default` - A default to be used if a field using this typesystem is missing from a parent `Object`.
* `properties` - A dictionary mapping string key names to typesystem or type values.
* `description` - A description for online documentation

Note that child properties are considered to be required if they do not have a `default` value.

### Array

Validates list or tuple input. A subclass of `list`.

* `items` - A typesystem or type or a list of typesystems or types.
* `additional_items` - Whether additional items past the end of the listed typesystem types are permitted.
* `min_items` - The minimum number of items the array must contain.
* `max_items` - The maximum number of items the array must contain.
* `unique_items` - Whether repeated items are permitted in the array.
* `description` - A description for online documentation

---

# Template & Static files

## Templates

## Static Files

---

# API Schemas

---

# Testing

---

# Event Hooks

---

# Components

---

# Performance

---

# Deployment

## The Development Server

## Running in Production

---

# Changelog

## 0.3 Release

* Added Authentication & Permissions support.
* Added Parsers & Renderers support, with content negotiation.
* Added HTTP Session support.
* Added `BEFORE_REQUEST` / `AFTER_REQUEST` settings.
* Added `SCHEMA` settings.
* Added support for using `Injector` component inside a handler.

Note: Because we now support configurable renderers, there's a difference in
the behaviour of returning plain data, or a Response without a `content_type` set.
Previously we would return HTML for strings/bytes, and JSON for anything else.
Now, JSON is the default for everything, unless alternative renderers are
specified. See the "Renderers & Parsers" and "Requests & Responses" section
for more detail.

## 0.2 Release

* Added `asyncio` support.
* Added `app.main()`.
* Added `Session` support for both SQLAlchemy and DjangoORM backends.
* Added proper support for registering commands, and using components in command handler functions.
* Added proper support for registering new components, and separating component interfaces from component implementations.
* Introduced `from apistar.frameworks.wsgi import WSGIApp as App` instead of `from apistar import App`.
* Introduced `from apistar.frameworks.asyncio import ASyncIOApp as App` instead of `from apistar import App`.
* Changed `apistar new --layout [minimal|standard]` to `apistar new --framework [wsgi|asyncio]`.
* The TestClient() class now explicitly requires the app instance to be passed as an argument.
* Dropped overloaded typesystem classes. Use eg. `typesystem.String` for declarations and `typesystem.string()` for inlines.
* Dropped single-lookup component `Template`. Just use `Templates` instead.
* Dropped single-lookup component `Setting`. Just use `Settings` instead.
* Dropped unneccessary `ResponseData` annotation.
* Dropped `WSGIResponse`. Either return data or a `Response`.
* Dropped `build()` method on components. See the docs for information on creating and registering components.
* Rationalized the 'TEMPLATES' and 'STATICS' settings.

---

# Development

To work on the API Star codebase, you'll want to clone the repository,
and create a Python virtualenv with the project requirements installed:

```bash
$ git clone git@github.com:tomchristie/apistar.git
$ cd apistar
$ ./scripts/setup
```

To run the continuous integration tests and code linting:

```bash
$ ./scripts/test
$ ./scripts/lint
```

---

<p align="center"><i>API Star is <a href="https://github.com/tomchristie/apistar/blob/master/LICENSE.md">BSD licensed</a> code.<br/>Designed & built in Brighton, England.</i><br/>&mdash; ⭐️ &mdash;</p>

[techempower]: https://www.techempower.com/benchmarks/#section=data-r14&hw=ph&test=json

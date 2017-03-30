# API Star ✨🚀✨🌟

A smart Web API framework, designed for Python 3.

[![Build Status](https://travis-ci.org/tomchristie/apistar.svg?branch=master)](https://travis-ci.org/tomchristie/apistar)
[![Package version](https://badge.fury.io/py/apistar.svg)](pypi.python.org/pypi/apistar)
[![Python versions](https://img.shields.io/pypi/pyversions/apistar.svg)](pypi.python.org/pypi/apistar)

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

API Star allows you to dynamically inject various information into your views
using type annotation.

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

| Component    | Description |
| ------------ | ----------- |
| Request      | The HTTP request. Includes `.method`, `.url` and `.headers` attributes. |
| Headers      | The request headers, returned as a dictionary-like object. |
| Header       | Lookup a single request header, corresponding to the argument name. Returns a string or `None`. |
| QueryParams  | The request query parameters, returned as a dictionary-like object. |
| QueryParam   | Lookup a single query parameter, corresponding to the argument name. Returns a string or `None`. |

---

# Responses

By default API star expects view to return plain data, and will return
`200 OK` responses. You can instead set the status code or headers by
annotating the view as returning a `Response`.

    def create_project() -> Response:
        data = {'name': 'new project', 'id': 123}
        headers = {'Location', 'http://example.com/project/123/'}
        return Response(data, status=201, headers=headers)

---

# URL Routing

Use `{curly_braces}` in your URL conf to include a URL path parameter.

    def echo_username(username):
        return {'message': f'Welcome, {username}!'}

    app = App(routes=[
        Route('/{username}/', 'GET', echo_username)
    ])

Use type annotation on the view method to include typed URL path parameters.

    users = {0: 'penny', 1: 'benny', 2: 'jenny'}

    def echo_username(user_id: int):
        username = users[user_id]
        return {'message': f'Welcome, {username}!'}

    app = App(routes=[
        Route('/{user_id}/', 'GET', echo_username)
    ])

Parameters which do not correspond to a URL path parameter will be treated as
query parameters.

    def echo_username(username):
        if username is None:
            return {'message': 'Welcome!'}
        return {'message': f'Welcome, {username}!'}

    app = App(routes=[
        Route('/hello/', 'GET', echo_username)
    ])

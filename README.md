# API Star ✨🚀✨🌟

A smart Web API framework, designed for Python 3.

[![PyPI version](https://badge.fury.io/py/apistar.svg)](https://badge.fury.io/py/apistar)
[![Build Status](https://travis-ci.org/tomchristie/apistar.svg?branch=master)](https://travis-ci.org/tomchristie/apistar)

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

# API Star

API Star is a smart Web API framework, designed for Python 3.

Install API Star:

    $ pip3 install apistar

Create a new project:

    $ apistar new myproject --template minimal
    myproject/app.py
    myproject/tests.py
    $ cd myproject
    $ cat app.py
    from apistar import App, Response, Route

    def welcome() -> Response:
        return Response({'message': 'Welcome to API Star!'})

    app = App(routes=[
        Route('/', 'get', welcome)
    ])

Run the application:

    $ apistar run
    Running at http://localhost:8080/

Run the tests:

    $ apistar test
    tests.py .
    ===== 1 passed in 0.01 seconds =====

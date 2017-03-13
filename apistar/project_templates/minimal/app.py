from apistar import App, Route, Response


def welcome() -> Response:
    return Response({'message': 'Welcome to API Star!'})


app = App(routes=[
    Route('/', 'get', welcome)
])

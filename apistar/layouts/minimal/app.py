from apistar import App, Route


def welcome():
    return {'message': 'Welcome to API Star!'}


routes = [
    Route('/', 'GET', welcome)
]

app = App(routes=routes)

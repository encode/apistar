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

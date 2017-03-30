from apistar import App, Route


def welcome():
    return {'message': 'Welcome to API Star!'}


app = App(routes=[
    Route('/', 'GET', welcome)
])

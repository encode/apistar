from apistar import Route
from project.views import welcome


routes = [
    Route('/', 'get', welcome)
]

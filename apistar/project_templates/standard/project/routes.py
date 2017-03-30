from apistar import Route
from project.views import welcome


routes = [
    Route('/', 'GET', welcome)
]

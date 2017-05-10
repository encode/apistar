from apistar import Route, Include
from apistar.docs import docs_routes
from apistar.statics import static_routes
from project.views import welcome

routes = [
    Route('/', 'GET', welcome),
    Include('/docs', docs_routes),
    Include('/static', static_routes)
]

from apistar.interfaces import Route, Router, Lookup
from werkzeug.routing import Rule, Map
import inspect
import typing
import uritemplate


class WerkzeugRouter(Router):
    def __init__(self, routes: typing.Sequence[Route]) -> None:
        rules = []
        views = {}
        converters = {
            int: 'int',
            float: 'float',
            str: 'string'
        }

        for path, method, view in routes:
            template = uritemplate.URITemplate(path)
            werkzeug_path = path[:]

            parameters = inspect.signature(view).parameters

            for arg in template.variable_names:
                assert arg in parameters, f'URL Argument "{arg}" missing from view {view}.'
                param = parameters[arg]
                converter = converters.get(param.annotation, 'path')
                template_format = '{%s}' % arg
                werkzeug_format = f'<{converter}:{arg}>'
                werkzeug_path = werkzeug_path.replace(template_format, werkzeug_format)

            name = view.__name__
            rule = Rule(werkzeug_path, methods=[method], endpoint=name)
            rules.append(rule)
            views[name] = view

        self._routes = routes
        self._adapter = Map(rules).bind('')
        self._views = views

    def lookup(self, path: str, method: str) -> Lookup:
        name, kwargs = self._adapter.match(path, method)
        view = self._views[name]
        return (view, kwargs)

    def reverse(self, identifier: str, kwargs: dict=None) -> str:
        return self._adapter.build(identifier, kwargs)

    def get_routes(self) -> typing.Sequence[Route]:
        return self._routes

import inspect
import typing
from urllib.parse import urlparse

import uritemplate
import werkzeug
from werkzeug.routing import Map, Rule

from apistar import exceptions
from apistar.interfaces import Lookup, PathWildcard, Route, Router


class WerkzeugRouter(Router):
    def __init__(self, routes: typing.Sequence[Route]) -> None:
        rules = []
        views = {}

        for path, method, view in routes:
            template = uritemplate.URITemplate(path)
            werkzeug_path = path[:]

            parameters = inspect.signature(view).parameters

            for arg in template.variable_names:
                converter = self._get_converter(parameters, arg, view)
                template_format = '{%s}' % arg
                werkzeug_format = '<%s:%s>' % (converter, arg)
                werkzeug_path = werkzeug_path.replace(template_format, werkzeug_format)

            name = view.__name__
            rule = Rule(werkzeug_path, methods=[method], endpoint=name)
            rules.append(rule)
            views[name] = view

        self._routes = routes
        self._adapter = Map(rules).bind('')
        self._views = views

    def _get_converter(self, parameters, arg, view):
        if arg not in parameters:
            msg = 'URL Argument "%s" missing from view "%s".' % (arg, view)
            raise exceptions.ConfigurationError(msg)

        annotation = parameters[arg].annotation

        if annotation is inspect.Parameter.empty:
            return 'string'
        elif issubclass(annotation, PathWildcard):
            return 'path'
        elif issubclass(annotation, str):
            return 'string'
        elif issubclass(annotation, int):
            return 'int'
        elif issubclass(annotation, float):
            return 'float'

        msg = 'Invalid type for path parameter "%s" in view "%s".' % (parameters[arg], view)
        raise exceptions.ConfigurationError(msg)

    def lookup(self, path: str, method: str) -> Lookup:
        try:
            name, kwargs = self._adapter.match(path, method)
        except werkzeug.exceptions.NotFound:
            raise exceptions.NotFound() from None
        except werkzeug.exceptions.MethodNotAllowed:
            raise exceptions.MethodNotAllowed() from None
        except werkzeug.routing.RequestRedirect as exc:
            path = urlparse(exc.new_url).path
            raise exceptions.Found(path) from None

        view = self._views[name]
        return (view, kwargs)

    def reverse_url(self, identifier: str, values: dict=None) -> str:
        try:
            return self._adapter.build(identifier, values)
        except werkzeug.routing.BuildError as exc:
            raise exceptions.NoReverseMatch(str(exc)) from None

    def get_routes(self) -> typing.Sequence[Route]:
        return self._routes

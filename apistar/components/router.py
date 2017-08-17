import collections
import inspect
import typing
from urllib.parse import urlparse

import uritemplate
import werkzeug
from werkzeug.routing import Map, Rule

from apistar import exceptions
from apistar.core import flatten_routes
from apistar.interfaces import Router
from apistar.types import HandlerLookup, PathWildcard, RouteConfig


class WerkzeugRouter(Router):
    def __init__(self, routes: RouteConfig) -> None:
        rules = []  # type: typing.List[Rule]
        views = {}  # type: typing.Dict[str, typing.Callable]

        for path, method, view, name in flatten_routes(routes):
            if name in views:
                msg = (
                    'Route wtih name "%s" exists more than once. Use an '
                    'explicit name="..." on the Route to avoid a conflict.'
                ) % name
                raise exceptions.ConfigurationError(msg)

            template = uritemplate.URITemplate(path)
            werkzeug_path = str(path)

            parameters = inspect.signature(view).parameters

            for arg in template.variable_names:
                converter = self._get_converter(parameters, arg, view)
                template_format = '{%s}' % arg
                werkzeug_format = '<%s:%s>' % (converter, arg)
                werkzeug_path = werkzeug_path.replace(template_format, werkzeug_format)

            rule = Rule(werkzeug_path, methods=[method], endpoint=name)
            rules.append(rule)
            views[name] = view

        self._routes = routes
        self._adapter = Map(rules).bind('')
        self._views = views

        # Use an MRU cache for router lookups.
        self._lookup_cache = collections.OrderedDict()  # type: collections.OrderedDict
        self._lookup_cache_size = 10000

    def _get_converter(self,
                       parameters: typing.Mapping[str, inspect.Parameter],
                       arg: str,
                       view: typing.Callable) -> str:
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

    def lookup(self, path: str, method: str) -> HandlerLookup:
        lookup_key = method + ' ' + path
        try:
            return self._lookup_cache[lookup_key]
        except KeyError:
            pass

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

        self._lookup_cache[lookup_key] = (view, kwargs)
        if len(self._lookup_cache) > self._lookup_cache_size:
            self._lookup_cache.pop(next(iter(self._lookup_cache)))  # pragma: nocover

        return (view, kwargs)

    def reverse_url(self, identifier: str, values: dict=None) -> str:
        try:
            return self._adapter.build(identifier, values)
        except werkzeug.routing.BuildError as exc:
            raise exceptions.NoReverseMatch(str(exc)) from None

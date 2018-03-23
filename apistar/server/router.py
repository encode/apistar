import inspect
import re
from urllib.parse import urlparse

import werkzeug
from werkzeug.routing import Map, Rule

from apistar import exceptions
from apistar.compat import dict_type
from apistar.server.core import Include, Route


class BaseRouter():
    def lookup(self, path: str, method: str):
        raise NotImplementedError()

    def reverse_url(self, name: str, **params) -> str:
        raise NotImplementedError()


class Router(BaseRouter):
    def __init__(self, routes):
        rules = []
        name_lookups = {}

        for path, name, route in self.walk_routes(routes):
            path_params = [
                item.strip('{}') for item in re.findall('{[^}]*}', path)
            ]
            args = inspect.signature(route.handler).parameters
            for path_param in path_params:
                if path_param.startswith('+'):
                    path = path.replace(
                        '{%s}' % path_param,
                        "<path:%s>" % path_param.lstrip('+')
                    )
                elif path_param in args and args[path_param].annotation is int:
                    path = path.replace(
                        '{%s}' % path_param,
                        "<int:%s>" % path_param
                    )
                elif path_param in args and args[path_param].annotation is float:
                    path = path.replace(
                        '{%s}' % path_param,
                        "<float:%s>" % path_param
                    )
                else:
                    path = path.replace(
                        '{%s}' % path_param,
                        "<string:%s>" % path_param
                    )

            rule = Rule(path, methods=[route.method], endpoint=name)
            rules.append(rule)
            name_lookups[name] = route

        self.adapter = Map(rules).bind('')
        self.name_lookups = name_lookups

        # Use an MRU cache for router lookups.
        self._lookup_cache = dict_type()
        self._lookup_cache_size = 10000

    def walk_routes(self, routes, url_prefix='', name_prefix=''):
        walked = []
        for item in routes:
            if isinstance(item, Route):
                result = (url_prefix + item.url, name_prefix + item.name, item)
                walked.append(result)
            elif isinstance(item, Include):
                result = self.walk_routes(
                    item.routes,
                    url_prefix + item.url,
                    name_prefix + item.name + ':'
                )
                walked.extend(result)
        return walked

    def lookup(self, path: str, method: str):
        lookup_key = method + ' ' + path
        try:
            return self._lookup_cache[lookup_key]
        except KeyError:
            pass

        try:
            name, path_params = self.adapter.match(path, method)
        except werkzeug.exceptions.NotFound:
            raise exceptions.NotFound() from None
        except werkzeug.exceptions.MethodNotAllowed:
            raise exceptions.MethodNotAllowed() from None
        except werkzeug.routing.RequestRedirect as exc:
            path = urlparse(exc.new_url).path
            raise exceptions.Found(path) from None

        route = self.name_lookups[name]

        self._lookup_cache[lookup_key] = (route, path_params)
        if len(self._lookup_cache) > self._lookup_cache_size:
            self._lookup_cache.pop(next(iter(self._lookup_cache)))

        return (route, path_params)

    def reverse_url(self, name: str, **params) -> str:
        try:
            return self.adapter.build(name, params)
        except werkzeug.routing.BuildError as exc:
            raise exceptions.NoReverseMatch(str(exc)) from None

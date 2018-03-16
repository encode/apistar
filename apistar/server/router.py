from urllib.parse import urlparse

import werkzeug
from werkzeug.routing import Map, Rule

from apistar import Document, exceptions
from apistar.compat import dict_type


class BaseRouter():
    def lookup(self, path: str, method: str):
        raise NotImplementedError()

    def reverse_url(self, name: str, **params) -> str:
        raise NotImplementedError()


class Router(BaseRouter):
    def __init__(self, document: Document):
        rules = []
        name_lookups = {}

        for link, name, sections in document.walk_links():
            path = link.url
            method = link.method

            for field in link.get_path_fields():
                if '{%s}' % field.name in path:
                    path = path.replace(
                        '{%s}' % field.name,
                        "<%s>" % field.name
                    )
                elif '{+%s}' % field.name in path:
                    path = path.replace(
                        '{+%s}' % field.name,
                        "<path:%s>" % field.name
                    )

            rule = Rule(path, methods=[method], endpoint=name)
            rules.append(rule)
            name_lookups[name] = (link, link.handler)

        self.adapter = Map(rules).bind('')
        self.name_lookups = name_lookups

        # Use an MRU cache for router lookups.
        self._lookup_cache = dict_type()
        self._lookup_cache_size = 10000

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

        (link, handler) = self.name_lookups[name]

        self._lookup_cache[lookup_key] = (link, handler, path_params)
        if len(self._lookup_cache) > self._lookup_cache_size:
            self._lookup_cache.pop(next(iter(self._lookup_cache)))

        return (link, handler, path_params)

    def reverse_url(self, name: str, **params) -> str:
        try:
            return self.adapter.build(name, params)
        except werkzeug.routing.BuildError as exc:
            raise exceptions.NoReverseMatch(str(exc)) from None

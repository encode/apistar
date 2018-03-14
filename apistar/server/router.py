from urllib.parse import urlparse

import werkzeug
from werkzeug.routing import Map, Rule

from apistar import Document, exceptions, types
from apistar.compat import dict_type


class Router():
    def __init__(self, document: Document):
        rules = []
        name_lookups = {}

        for link, name, sections in document.walk_links():
            path = link.url
            method = link.method

            for field in link.path_fields():
                converter = self.get_converter(field)
                template_format = '{%s}' % field.name
                werkzeug_format = '<%s:%s>' % (converter, field.name)
                path = path.replace(template_format, werkzeug_format)

            rule = Rule(path, methods=[method], endpoint=name)
            rules.append(rule)
            name_lookups[name] = (link, link.handler)

        self.adapter = Map(rules).bind('')
        self.name_lookups = name_lookups

        # Use an MRU cache for router lookups.
        self._lookup_cache = dict_type()
        self._lookup_cache_size = 10000

    def get_converter(self, field):
        if isinstance(field.schema, types.Integer):
            return 'int'
        elif isinstance(field.schema, types.Number):
            return 'float'
        return 'string'

    def lookup(self, path: str, method: str):
        lookup_key = method + ' ' + path
        try:
            return self._lookup_cache[lookup_key]
        except KeyError:
            pass

        try:
            name, path_kwargs = self.adapter.match(path, method)
        except werkzeug.exceptions.NotFound:
            raise exceptions.NotFound() from None
        except werkzeug.exceptions.MethodNotAllowed:
            raise exceptions.MethodNotAllowed() from None
        except werkzeug.routing.RequestRedirect as exc:
            path = urlparse(exc.new_url).path
            raise exceptions.Found(path) from None

        (link, handler) = self.name_lookups[name]

        for field in link.path_fields():
            if (field.schema is not None) and (field.id in path_kwargs):
                try:
                    path_kwargs[field.id] = field.schema.validate(path_kwargs[field.id])
                except exceptions.ValidationError as exc:
                    raise exceptions.NotFound(detail=exc.detail) from None

        self._lookup_cache[lookup_key] = (link, handler, path_kwargs)
        if len(self._lookup_cache) > self._lookup_cache_size:
            self._lookup_cache.pop(next(iter(self._lookup_cache)))

        return (link, handler, path_kwargs)

    def reverse_url(self, name: str, values: dict=None) -> str:
        try:
            return self.adapter.build(name, values)
        except werkzeug.routing.BuildError as exc:
            raise exceptions.NoReverseMatch(str(exc)) from None

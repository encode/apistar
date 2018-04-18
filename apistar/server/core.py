import inspect
import re

from apistar import http, types, validators
from apistar.document import Document, Field, Link, Section


class Route():
    def __init__(self, url, method, handler, name=None, documented=True, standalone=False, link=None):
        self.url = url
        self.method = method
        self.handler = handler
        self.name = name or handler.__name__
        self.documented = documented
        self.standalone = standalone
        if link is None:
            self.link = self.generate_link(url, method, handler, self.name)
        else:
            self.link = link

    def generate_link(self, url, method, handler, name):
        fields = self.generate_fields(url, method, handler)
        encoding = None
        if any([f.location == 'body' for f in fields]):
            encoding = 'application/json'
        return Link(
            url=url,
            method=method,
            name=name,
            encoding=encoding,
            fields=fields,
            description=handler.__doc__
        )

    def generate_fields(self, url, method, handler):
        fields = []
        path_names = [
            item.strip('{}').lstrip('+') for item in re.findall('{[^}]*}', url)
        ]
        parameters = inspect.signature(handler).parameters
        for name, param in parameters.items():
            if name in path_names:
                schema = {
                    param.empty: None,
                    int: validators.Integer(),
                    float: validators.Number(),
                    str: validators.String()
                }[param.annotation]
                field = Field(name=name, location='path', schema=schema)
                fields.append(field)

            elif param.annotation in (param.empty, int, float, bool, str, http.QueryParam):
                if param.default is param.empty:
                    kwargs = {}
                elif param.default is None:
                    kwargs = {'default': None, 'allow_null': True}
                else:
                    kwargs = {'default': param.default}
                schema = {
                    param.empty: None,
                    int: validators.Integer(**kwargs),
                    float: validators.Number(**kwargs),
                    bool: validators.Boolean(**kwargs),
                    str: validators.String(**kwargs),
                    http.QueryParam: validators.String(**kwargs),
                }[param.annotation]
                field = Field(name=name, location='query', schema=schema)
                fields.append(field)

            elif issubclass(param.annotation, types.Type):
                field = Field(name=name, location='body', schema=param.annotation.validator)
                fields.append(field)

        return fields


class Include():
    def __init__(self, url, name, routes, documented=True, section=None):
        self.url = url
        self.name = name
        self.routes = routes
        self.documented = documented

        if section is None:
            self.section = self.generate_section(routes, name)
        else:
            self.section = None

    def generate_section(self, routes, name):
        content = self.generate_content(routes)
        return Section(name=name, content=content)

    def generate_content(self, routes):
        content = []
        for item in routes:
            if isinstance(item, Route):
                if item.link is not None:
                    content.append(item.link)
            elif isinstance(item, Section):
                if item.section is not None:
                    content.append(item.section)
        return content


def generate_document(routes):
    content = []
    for item in routes:
        if isinstance(item, Route) and item.documented:
            content.append(item.link)
        elif isinstance(item, Include) and item.documented:
            content.append(item.section)
    return Document(content=content)


def bind(document, bindings, name_prefix=''):
    """
    Given a document and a map of {"section:link": handler} return a
    list of `Include` and `Route` to use for routing the application.
    """
    routes = []
    for item in document.content:
        if isinstance(item, Link):
            handler = bindings[name_prefix + item.name]
            routes.append(Route(
                url=item.url,
                method=item.method,
                name=item.name,
                handler=handler,
                link=item
            ))
        elif isinstance(item, Section):
            section_name_prefix = name_prefix + item.name + ':'
            children = bind(item, bindings, section_name_prefix)
            routes.append(Include(
                url='',
                name=item.name,
                routes=children
            ))
    return routes

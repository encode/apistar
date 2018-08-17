import inspect
import re
import typing

from apistar import http, types, validators
from apistar.document import Document, Field, Link, Response, Section


class Route():
    def __init__(self, url, method, handler, name=None, documented=True, standalone=False):
        self.url = url
        self.method = method
        self.handler = handler
        self.name = name or handler.__name__
        self.documented = documented
        self.standalone = standalone
        self.link = self.generate_link(url, method, handler, self.name)

    def generate_link(self, url, method, handler, name):
        fields = self.generate_fields(url, method, handler)
        response = self.generate_response(handler)
        encoding = None
        if any([f.location == 'body' for f in fields]):
            encoding = 'application/json'
        return Link(
            url=url,
            method=method,
            name=name,
            encoding=encoding,
            fields=fields,
            response=response,
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
                if method in ('GET', 'DELETE'):
                    for name, validator in param.annotation.validator.properties.items():
                        field = Field(name=name, location='query', schema=validator)
                        fields.append(field)
                else:
                    field = Field(name=name, location='body', schema=param.annotation.validator)
                    fields.append(field)

        return fields

    def generate_response(self, handler):
        annotation = inspect.signature(handler).return_annotation
        annotation = self.coerce_generics(annotation)

        if not (issubclass(annotation, types.Type) or isinstance(annotation, validators.Validator)):
            return None

        return Response(encoding='application/json', status_code=200, schema=annotation)

    def coerce_generics(self, annotation):
        origin = getattr(annotation, '__origin__', annotation)
        if (
            isinstance(origin, type) and
            issubclass(origin, typing.List) and
            getattr(annotation, '__args__', None) and
            issubclass(annotation.__args__[0], types.Type)
        ):
            return validators.Array(items=annotation.__args__[0])
        return annotation


class Include():
    def __init__(self, url, name, routes, documented=True):
        self.url = url
        self.name = name
        self.routes = routes
        self.documented = documented
        self.section = self.generate_section(routes, name)

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
            for link in item.section.get_links():
                link.url = item.url + link.url
    return Document(content=content)

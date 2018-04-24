import inspect
import re

from apistar import http, types
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
            annotation = param.annotation
            if name in path_names:
                if annotation is http.PathParam:
                    annotation = http.ValidatedPathParam[str]

                if annotation is param.empty:
                    schema = None
                else:
                    if annotation in (int, float, str):
                        annotation = http.ValidatedPathParam[annotation]
                    elif not _issubclass(annotation, http.PathParamBase):
                        raise TypeError('Path param annotation has to be int, float, str or http.ValidatedPathParam[V]')
                    schema = annotation.get_validator()
                field = Field(name=name, location='path', schema=schema)
                fields.append(field)

            elif (annotation in (param.empty, int, float, bool, str, http.QueryParam)
                  or _issubclass(annotation, http.QueryParamBase)):
                if annotation is http.QueryParam:
                    annotation = http.ValidatedQueryParam[str]
                if param.default is param.empty:
                    kwargs = {}
                elif param.default is None:
                    kwargs = {'default': None, 'allow_null': True}
                else:
                    kwargs = {'default': param.default}

                if annotation is param.empty:
                    schema = None
                else:
                    if not _issubclass(annotation, http.QueryParamBase):
                        annotation = http.ValidatedQueryParam[annotation]
                    schema = annotation.get_validator(**kwargs)
                field = Field(name=name, location='query', schema=schema)
                fields.append(field)
            elif issubclass(annotation, types.Type):
                if method in ('GET', 'DELETE'):
                    for name, validator in annotation.validator.properties.items():
                        field = Field(name=name, location='query', schema=validator)
                        fields.append(field)
                else:
                    field = Field(name=name, location='body', schema=annotation.validator)
                    fields.append(field)

        return fields


def _issubclass(obj, cls):
    return inspect.isclass(obj) and issubclass(obj, cls)


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

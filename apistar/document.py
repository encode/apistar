import re
import typing

from apistar.types import Validator


class Document():
    def __init__(self,
                 content: typing.Sequence[typing.Union['Section', 'Link']]=None,
                 url: str='',
                 title: str='',
                 description: str='',
                 version: str=''):
        self.content = [] if (content is None) else list(content)
        self.url = url
        self.title = title
        self.description = description
        self.version = version

    def links(self):
        return [item for item in self.content if isinstance(item, Link)]

    def sections(self):
        return [item for item in self.content if isinstance(item, Section)]

    def walk_links(self):
        links = []
        for item in self.content:
            if isinstance(item, Link):
                sections = ()
                links.append((sections, item))
            else:
                links.extend(item.walk_links())
        return links

    def lookup_link(self, name: str):
        names = name.split(':')
        for sections, link in self.walk_links():
            link_names = [section.name for section in sections] + [link.name]
            if link_names == names:
                return link
        raise ValueError('Link "%s" not found in document.' % name)


class Section():
    def __init__(self,
                 content: typing.Sequence[typing.Union['Section', 'Link']]=None,
                 name: str='',
                 title: str='',
                 description: str=''):
        self.content = [] if (content is None) else list(content)
        self.name = name
        self.title = title
        self.description = description

    def links(self):
        return [item for item in self.content if isinstance(item, Link)]

    def sections(self):
        return [item for item in self.content if isinstance(item, Section)]

    def walk_links(self, previous_sections=()):
        links = []
        sections = previous_sections + (self,)
        for item in self.content:
            if isinstance(item, Link):
                links.append((sections, item))
            else:
                links.extend(item.walk_links(previous_sections=sections))
        return links


class Link():
    """
    Links represent the actions that a client may perform.
    """
    def __init__(self,
                 url,
                 method,
                 handler=None,
                 name='',
                 encoding='',
                 title='',
                 description='',
                 fields: typing.Sequence['Field']=None):
        method = method.upper()
        fields = [] if (fields is None) else list(fields)

        url_path_names = set([
            item.strip('{}') for item in re.findall('{[^}]*}', url)
        ])
        field_path_names = set([
            field.name for field in fields if field.location == 'path'
        ])

        assert method in (
            'GET', 'POST', 'PUT', 'PATCH',
            'DELETE', 'OPTIONS', 'HEAD', 'TRACE'
        )
        assert url_path_names == field_path_names

        self.url = url
        self.method = method
        self.handler = handler
        self.name = name if name else handler.__name__
        self.encoding = encoding
        self.title = title
        self.description = description
        self.fields = fields

    def path_fields(self):
        return [field for field in self.fields if field.location == 'path']

    def query_fields(self):
        return [field for field in self.fields if field.location == 'query']

    def body_field(self):
        body_fields = [field for field in self.fields if field.location == 'body']
        return next(body_fields, default=None)


class Field():
    def __init__(self,
                 name: str,
                 location: str,
                 title: str='',
                 description: str='',
                 required: bool=False,
                 schema: Validator=None,
                 example: typing.Any=None):
        assert location in ('path', 'query', 'body')
        assert required if (location == 'path') else True

        self.name = name
        self.title = title
        self.description = description
        self.location = location
        self.required = required
        self.schema = schema
        self.example = example

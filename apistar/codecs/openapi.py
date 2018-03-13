from apistar import types
from apistar.codecs import BaseCodec, JSONSchemaCodec
from apistar.codecs.jsonschema import JSON_SCHEMA
from apistar.compat import dict_type
from apistar.document import Document, Link, Field, Section
from apistar.exceptions import ParseError
from urllib.parse import urljoin, urlparse
import json
import re


SCHEMA_REF = types.Object(
    properties={'$ref': types.String(pattern='^#/components/schemas/')}
)


OPEN_API = types.Object(
    self_ref='OpenAPI',
    title='OpenAPI',
    properties=[
        ('openapi', types.String()),
        ('info', types.Ref('Info')),
        ('servers', types.Array(items=types.Ref('Server'))),
        ('paths', types.Ref('Paths')),
        ('components', types.Ref('Components')),
        ('security', types.Ref('SecurityRequirement')),
        ('tags', types.Array(items=types.Ref('Tag'))),
        ('externalDocs', types.Ref('ExternalDocumentation'))
    ],
    required=['openapi', 'info'],
    definitions={
        'Info': types.Object(
            properties=[
                ('title', types.String()),
                ('description', types.String(format='textarea')),
                ('termsOfService', types.String(format='url')),
                ('contact', types.Ref('Contact')),
                ('license', types.Ref('License')),
                ('version', types.String())
            ],
            required=['title', 'version']
        ),
        'Contact': types.Object(
            properties=[
                ('name', types.String()),
                ('url', types.String(format='url')),
                ('email', types.String(format='email'))
            ]
        ),
        'License': types.Object(
            properties=[
                ('name', types.String()),
                ('url', types.String(format='url'))
            ],
            required=['name']
        ),
        'Server': types.Object(
            properties=[
                ('url', types.String()),
                ('description', types.String(format='textarea')),
                ('variables', types.Object(additional_properties=types.Ref('ServerVariable')))
            ],
            required=['url']
        ),
        'ServerVariable': types.Object(
            properties=[
                ('enum', types.Array(items=types.String())),
                ('default', types.String()),
                ('description', types.String(format='textarea'))
            ],
            required=['default']
        ),
        'Paths': types.Object(
            pattern_properties=[
                ('^/', types.Ref('Path'))  # TODO: Path | ReferenceObject
            ]
        ),
        'Path': types.Object(
            properties=[
                ('summary', types.String()),
                ('description', types.String(format='textarea')),
                ('get', types.Ref('Operation')),
                ('put', types.Ref('Operation')),
                ('post', types.Ref('Operation')),
                ('delete', types.Ref('Operation')),
                ('options', types.Ref('Operation')),
                ('head', types.Ref('Operation')),
                ('patch', types.Ref('Operation')),
                ('trace', types.Ref('Operation')),
                ('servers', types.Array(items=types.Ref('Server'))),
                ('parameters', types.Array(items=types.Ref('Parameter')))  # TODO: Parameter | ReferenceObject
            ]
        ),
        'Operation': types.Object(
            properties=[
                ('tags', types.Array(items=types.String())),
                ('summary', types.String()),
                ('description', types.String(format='textarea')),
                ('externalDocs', types.Ref('ExternalDocumentation')),
                ('operationId', types.String()),
                ('parameters', types.Array(items=types.Ref('Parameter'))),  # TODO: Parameter | ReferenceObject
                ('requestBody', types.Ref('RequestBody')),  # TODO: RequestBody | ReferenceObject
                # TODO: 'responses'
                # TODO: 'callbacks'
                ('deprecated', types.Boolean()),
                ('security', types.Array(types.Ref('SecurityRequirement'))),
                ('servers', types.Array(items=types.Ref('Server')))
            ]
        ),
        'ExternalDocumentation': types.Object(
            properties=[
                ('description', types.String(format='textarea')),
                ('url', types.String(format='url'))
            ],
            required=['url']
        ),
        'Parameter': types.Object(
            properties=[
                ('name', types.String()),
                ('in', types.String(enum=['query', 'header', 'path', 'cookie'])),
                ('description', types.String(format='textarea')),
                ('required', types.Boolean()),
                ('deprecated', types.Boolean()),
                ('allowEmptyValue', types.Boolean()),
                ('schema', JSON_SCHEMA | SCHEMA_REF),
                ('example', types.Any())
                # TODO: Other fields
            ],
            required=['name', 'in']
        ),
        'RequestBody': types.Object(
            properties=[
                ('description', types.String()),
                ('content', types.Object(additional_properties=types.Ref('MediaType'))),
                ('required', types.Boolean())
            ]
        ),
        'MediaType': types.Object(
            properties=[
                ('schema', JSON_SCHEMA | SCHEMA_REF),
                ('example', types.Any())
                # TODO 'examples', 'encoding'
            ]
        ),
        'Components': types.Object(
            properties=[
                ('schemas', types.Object(additional_properties=JSON_SCHEMA)),
            ]
        ),
        'Tag': types.Object(
            properties=[
                ('name', types.String()),
                ('description', types.String(format='textarea')),
                ('externalDocs', types.Ref('ExternalDocumentation'))
            ],
            required=['name']
        ),
        'SecurityRequirement': types.Object(
            additional_properties=types.Array(items=types.String())
        )
    }
)


METHODS = [
    'get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace'
]


def lookup(value, keys, default=None):
    for key in keys:
        try:
            value = value[key]
        except (KeyError, IndexError, TypeError):
            return default
    return value


def _relative_url(base_url, url):
    """
    Return a graceful link for a URL relative to a base URL.

    * If the have the same scheme and hostname, return the path & query params.
    * Otherwise return the full URL.
    """
    base_prefix = '%s://%s' % urlparse(base_url or '')[0:2]
    url_prefix = '%s://%s' % urlparse(url or '')[0:2]
    if base_prefix == url_prefix and url_prefix != '://':
        return url[len(url_prefix):]
    return url


def _simple_slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    text = re.sub(r'[_]+', '_', text)
    return text.strip('_')


class OpenAPICodec(BaseCodec):
    media_type = 'application/vnd.oai.openapi'
    format = 'openapi'

    def decode(self, bytestring, **options):
        try:
            data = json.loads(bytestring.decode('utf-8'))
        except ValueError as exc:
            raise ParseError('Malformed JSON. %s' % exc)

        openapi = OPEN_API.validate(data)
        title = lookup(openapi, ['info', 'title'])
        description = lookup(openapi, ['info', 'description'])
        version = lookup(openapi, ['info', 'version'])
        base_url = lookup(openapi, ['servers', 0, 'url'])
        schema_definitions = self.get_schema_definitions(openapi)
        sections = self.get_sections(openapi, base_url, schema_definitions)
        return Document(title=title, description=description, version=version, url=base_url, sections=sections)

    def get_schema_definitions(self, openapi):
        definitions = {}
        schemas = lookup(openapi, ['components', 'schemas'], {})
        for key, value in schemas.items():
            definitions[key] = JSONSchemaCodec().decode_from_data_structure(value)
        return definitions

    def get_sections(self, openapi, base_url, schema_definitions):
        """
        Return all the links in the document, layed out by tag and operationId.
        """
        links = dict_type()

        for path, path_info in openapi.get('paths', {}).items():
            operations = {
                key: path_info[key] for key in path_info
                if key in METHODS
            }
            for operation, operation_info in operations.items():
                tag = lookup(operation_info, ['tags', 0], default='')
                link = self.get_link(base_url, path, path_info, operation, operation_info, schema_definitions)
                if link is None:
                    continue

                if tag not in links:
                    links[tag] = []
                links[tag].append(link)

        return [
            Section(id=_simple_slugify(key), title=key.title(), links=value)
            for key, value in links.items()
        ]

    def get_link(self, base_url, path, path_info, operation, operation_info, schema_definitions):
        """
        Return a single link in the document.
        """
        id = operation_info.get('operationId')
        title = operation_info.get('summary')
        description = operation_info.get('description')

        if id is None:
            id = _simple_slugify(title)
            if not id:
                return None

        # Allow path info and operation info to override the base url.
        base_url = lookup(path_info, ['servers', 0, 'url'], default=base_url)
        base_url = lookup(operation_info, ['servers', 0, 'url'], default=base_url)

        # Parameters are taken both from the path info, and from the operation.
        parameters = path_info.get('parameters', [])
        parameters += operation_info.get('parameters', [])

        fields = [
            self.get_field(parameter, schema_definitions)
            for parameter in parameters
        ]

        # TODO: Handle media type generically here...
        body_schema = lookup(operation_info, ['requestBody', 'content', 'application/json', 'schema'])

        encoding = None
        if body_schema:
            encoding = 'application/json'
            if '$ref' in body_schema:
                ref = body_schema['$ref'][len('#/components/schemas/'):]
                schema = schema_definitions.get(ref)
            else:
                schema = JSONSchemaCodec().decode_from_data_structure(body_schema)
            if isinstance(schema, types.Object):
                for key, value in schema.properties.items():
                    fields += [Field(name=key, location='form', schema=value)]

        return Link(
            id=id,
            url=urljoin(base_url, path),
            method=operation,
            title=title,
            description=description,
            fields=fields,
            encoding=encoding
        )

    def get_field(self, parameter, schema_definitions):
        """
        Return a single field in a link.
        """
        name = parameter.get('name')
        location = parameter.get('in')
        description = parameter.get('description')
        required = parameter.get('required', False)
        schema = parameter.get('schema')
        example = parameter.get('example')

        if schema is not None:
            if '$ref' in schema:
                ref = schema['$ref'][len('#/components/schemas/'):]
                schema = schema_definitions.get(ref)
            else:
                schema = JSONSchemaCodec().decode_from_data_structure(schema)

        return Field(
            name=name,
            location=location,
            description=description,
            required=required,
            schema=schema,
            example=example
        )

    def encode(self, document, **options):
        paths = self.get_paths(document)
        openapi = OpenAPI.validate({
            'openapi': '3.0.0',
            'info': {
                'version': document.version,
                'title': document.title,
                'description': document.description
            },
            'servers': [{
                'url': document.url
            }],
            'paths': paths
        })

        kwargs = {
            'ensure_ascii': False,
            'indent': 4,
            'separators': (',', ': ')
        }
        return json.dumps(openapi, **kwargs).encode('utf-8')

    def get_paths(self, document):
        paths = dict_type()

        for operation_id, link in document.links.items():
            url = urlparse(link.url)
            if url.path not in paths:
                paths[url.path] = {}
            paths[url.path][link.action] = self.get_operation(link, operation_id)

        for tag, links in document.data.items():
            for operation_id, link in links.links.items():
                url = urlparse(link.url)
                if url.path not in paths:
                    paths[url.path] = {}
                paths[url.path][link.action] = self.get_operation(link, operation_id, tag=tag)

        return paths

    def get_operation(self, link, operation_id, tag=None):
        operation = {
            'operationId': operation_id
        }
        if link.title:
            operation['summary'] = link.title
        if link.description:
            operation['description'] = link.description
        if tag:
            operation['tags'] = [tag]
        if link.fields:
            operation['parameters'] = [self.get_parameter(field) for field in link.fields]
        return operation

    def get_parameter(self, field):
        parameter = {
            'name': field.name,
            'in': field.location
        }
        if field.required:
            parameter['required'] = True
        if field.description:
            parameter['description'] = field.description
        if field.schema:
            parameter['schema'] = JSONSchemaCodec().encode_to_data_structure(field.schema)
        return parameter

import json
import re
from urllib.parse import urljoin, urlparse

from apistar import validators
from apistar.codecs import BaseCodec, JSONSchemaCodec
from apistar.codecs.jsonschema import JSON_SCHEMA
from apistar.compat import dict_type
from apistar.document import Document, Field, Link, Section
from apistar.parse import infer_json_or_yaml, parse_json, parse_yaml

SCHEMA_REF = validators.Object(
    properties={'$ref': validators.String(pattern='^#/components/schemas/')}
)
REQUESTBODY_REF = validators.Object(
    properties={'$ref': validators.String(pattern='^#/components/requestBodies/')}
)
RESPONSE_REF = validators.Object(
    properties={'$ref': validators.String(pattern='^#/components/responses/')}
)

OPEN_API = validators.Object(
    def_name='OpenAPI',
    title='OpenAPI',
    properties=[
        ('openapi', validators.String()),
        ('info', validators.Ref('Info')),
        ('servers', validators.Array(items=validators.Ref('Server'))),
        ('paths', validators.Ref('Paths')),
        ('components', validators.Ref('Components')),
        ('security', validators.Array(items=validators.Ref('SecurityRequirement'))),
        ('tags', validators.Array(items=validators.Ref('Tag'))),
        ('externalDocs', validators.Ref('ExternalDocumentation')),
    ],
    pattern_properties={
        '^x-': validators.Any(),
    },
    additional_properties=False,
    required=['openapi', 'info', 'paths'],
    definitions={
        'Info': validators.Object(
            properties=[
                ('title', validators.String()),
                ('description', validators.String(format='textarea')),
                ('termsOfService', validators.String(format='url')),
                ('contact', validators.Ref('Contact')),
                ('license', validators.Ref('License')),
                ('version', validators.String()),
            ],
            pattern_properties={
                '^x-': validators.Any(),
            },
            additional_properties=False,
            required=['title', 'version']
        ),
        'Contact': validators.Object(
            properties=[
                ('name', validators.String()),
                ('url', validators.String(format='url')),
                ('email', validators.String(format='email')),
            ],
            pattern_properties={
                '^x-': validators.Any(),
            },
            additional_properties=False,
        ),
        'License': validators.Object(
            properties=[
                ('name', validators.String()),
                ('url', validators.String(format='url')),
            ],
            required=['name'],
            pattern_properties={
                '^x-': validators.Any(),
            },
            additional_properties=False,
        ),
        'Server': validators.Object(
            properties=[
                ('url', validators.String()),
                ('description', validators.String(format='textarea')),
                ('variables', validators.Object(additional_properties=validators.Ref('ServerVariable'))),
            ],
            pattern_properties={
                '^x-': validators.Any(),
            },
            additional_properties=False,
            required=['url']
        ),
        'ServerVariable': validators.Object(
            properties=[
                ('enum', validators.Array(items=validators.String())),
                ('default', validators.String()),
                ('description', validators.String(format='textarea')),
            ],
            pattern_properties={
                '^x-': validators.Any(),
            },
            additional_properties=False,
            required=['default']
        ),
        'Paths': validators.Object(
            pattern_properties=[
                ('^/', validators.Ref('Path')),
                ('^x-', validators.Any()),
            ],
            additional_properties=False,
        ),
        'Path': validators.Object(
            properties=[
                ('summary', validators.String()),
                ('description', validators.String(format='textarea')),
                ('get', validators.Ref('Operation')),
                ('put', validators.Ref('Operation')),
                ('post', validators.Ref('Operation')),
                ('delete', validators.Ref('Operation')),
                ('options', validators.Ref('Operation')),
                ('head', validators.Ref('Operation')),
                ('patch', validators.Ref('Operation')),
                ('trace', validators.Ref('Operation')),
                ('servers', validators.Array(items=validators.Ref('Server'))),
                ('parameters', validators.Array(items=validators.Ref('Parameter'))),  # TODO: | ReferenceObject
            ],
            pattern_properties={
                '^x-': validators.Any(),
            },
            additional_properties=False,
        ),
        'Operation': validators.Object(
            properties=[
                ('tags', validators.Array(items=validators.String())),
                ('summary', validators.String()),
                ('description', validators.String(format='textarea')),
                ('externalDocs', validators.Ref('ExternalDocumentation')),
                ('operationId', validators.String()),
                ('parameters', validators.Array(items=validators.Ref('Parameter'))),  # TODO: | ReferenceObject
                ('requestBody', REQUESTBODY_REF | validators.Ref('RequestBody')),  # TODO: RequestBody | ReferenceObject
                ('responses', validators.Ref('Responses')),
                # TODO: 'callbacks'
                ('deprecated', validators.Boolean()),
                ('security', validators.Array(validators.Ref('SecurityRequirement'))),
                ('servers', validators.Array(items=validators.Ref('Server'))),
            ],
            pattern_properties={
                '^x-': validators.Any(),
            },
            additional_properties=False,
        ),
        'ExternalDocumentation': validators.Object(
            properties=[
                ('description', validators.String(format='textarea')),
                ('url', validators.String(format='url')),
            ],
            pattern_properties={
                '^x-': validators.Any(),
            },
            additional_properties=False,
            required=['url']
        ),
        'Parameter': validators.Object(
            properties=[
                ('name', validators.String()),
                ('in', validators.String(enum=['query', 'header', 'path', 'cookie'])),
                ('description', validators.String(format='textarea')),
                ('required', validators.Boolean()),
                ('deprecated', validators.Boolean()),
                ('allowEmptyValue', validators.Boolean()),
                ('style', validators.String()),
                ('schema', JSON_SCHEMA | SCHEMA_REF),
                ('example', validators.Any()),
                # TODO: Other fields
            ],
            pattern_properties={
                '^x-': validators.Any(),
            },
            additional_properties=False,
            required=['name', 'in']
        ),
        'RequestBody': validators.Object(
            properties=[
                ('description', validators.String()),
                ('content', validators.Object(additional_properties=validators.Ref('MediaType'))),
                ('required', validators.Boolean()),
            ],
            pattern_properties={
                '^x-': validators.Any(),
            },
            additional_properties=False,
        ),
        'Responses': validators.Object(
            properties=[
                ('default', validators.Ref('Response') | RESPONSE_REF),
            ],
            pattern_properties=[
                ('^([1-5][0-9][0-9]|[1-5]XX)$', validators.Ref('Response') | RESPONSE_REF),
                ('^x-', validators.Any()),
            ],
            additional_properties=False,
        ),
        'Response': validators.Object(
            properties=[
                ('description', validators.String()),
                ('content', validators.Object(additional_properties=validators.Ref('MediaType'))),
                ('headers', validators.Object(additional_properties=validators.Ref('Header'))),
                # TODO: Header | ReferenceObject
                # TODO: links
            ],
            pattern_properties={
                '^x-': validators.Any(),
            },
            additional_properties=False,
        ),
        'MediaType': validators.Object(
            properties=[
                ('schema', JSON_SCHEMA | SCHEMA_REF),
                ('example', validators.Any()),
                # TODO 'examples', 'encoding'
            ],
            pattern_properties={
                '^x-': validators.Any(),
            },
            additional_properties=False,
        ),
        'Header': validators.Object(
            properties=[
                ('description', validators.String(format='textarea')),
                ('required', validators.Boolean()),
                ('deprecated', validators.Boolean()),
                ('allowEmptyValue', validators.Boolean()),
                ('style', validators.String()),
                ('schema', JSON_SCHEMA | SCHEMA_REF),
                ('example', validators.Any()),
                # TODO: Other fields
            ],
            pattern_properties={
                '^x-': validators.Any(),
            },
            additional_properties=False
        ),
        'Components': validators.Object(
            properties=[
                ('schemas', validators.Object(additional_properties=JSON_SCHEMA)),
                ('responses', validators.Object(additional_properties=validators.Ref('Response'))),
                ('parameters', validators.Object(additional_properties=validators.Ref('Parameter'))),
                ('requestBodies', validators.Object(additional_properties=validators.Ref('RequestBody'))),
                ('securitySchemes', validators.Object(additional_properties=validators.Ref('SecurityScheme'))),
                # TODO: Other fields
            ],
            pattern_properties={
                '^x-': validators.Any(),
            },
            additional_properties=False,
        ),
        'Tag': validators.Object(
            properties=[
                ('name', validators.String()),
                ('description', validators.String(format='textarea')),
                ('externalDocs', validators.Ref('ExternalDocumentation')),
            ],
            pattern_properties={
                '^x-': validators.Any(),
            },
            additional_properties=False,
            required=['name']
        ),
        'SecurityRequirement': validators.Object(
            additional_properties=validators.Array(items=validators.String()),
        ),
        'SecurityScheme': validators.Object(
            properties=[
                ('type', validators.String(enum=['apiKey', 'http', 'oauth2', 'openIdConnect'])),
                ('description', validators.String(format='textarea')),
                ('name', validators.String()),
                ('in', validators.String(enum=['query', 'header', 'cookie'])),
                ('scheme', validators.String()),
                ('bearerFormat', validators.String()),
                ('flows', validators.Any()),  # TODO: OAuthFlows
                ('openIdConnectUrl', validators.String()),
            ],
            pattern_properties={
                '^x-': validators.Any(),
            },
            additional_properties=False,
            required=['type']
        ),
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
    if text is None:
        return None
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    text = re.sub(r'[_]+', '_', text)
    return text.strip('_')


class OpenAPICodec(BaseCodec):
    media_type = 'application/vnd.oai.openapi'
    format = 'openapi'

    def decode(self, content, **options):
        base_format = infer_json_or_yaml(content)
        if base_format == 'json':
            data = parse_json(content, validator=OPEN_API)
        else:
            data = parse_yaml(content, validator=OPEN_API)

        title = lookup(data, ['info', 'title'])
        description = lookup(data, ['info', 'description'])
        version = lookup(data, ['info', 'version'])
        base_url = lookup(data, ['servers', 0, 'url'])
        schema_definitions = self.get_schema_definitions(data)
        content = self.get_content(data, base_url, schema_definitions)

        return Document(title=title, description=description, version=version, url=base_url, content=content)

    def get_schema_definitions(self, data):
        definitions = {}
        schemas = lookup(data, ['components', 'schemas'], {})
        for key, value in schemas.items():
            definitions[key] = JSONSchemaCodec().decode_from_data_structure(value)
        return definitions

    def get_content(self, data, base_url, schema_definitions):
        """
        Return all the links in the document, layed out by tag and operationId.
        """
        links_by_tag = dict_type()
        links = []

        for path, path_info in data.get('paths', {}).items():
            operations = {
                key: path_info[key] for key in path_info
                if key in METHODS
            }
            for operation, operation_info in operations.items():
                tag = lookup(operation_info, ['tags', 0])
                link = self.get_link(base_url, path, path_info, operation, operation_info, schema_definitions)
                if link is None:
                    continue

                if tag is None:
                    links.append(link)
                elif tag not in links_by_tag:
                    links_by_tag[tag] = [link]
                else:
                    links_by_tag[tag].append(link)

        sections = [
            Section(name=_simple_slugify(tag), title=tag.title(), content=links)
            for tag, links in links_by_tag.items()
        ]
        return links + sections

    def get_link(self, base_url, path, path_info, operation, operation_info, schema_definitions):
        """
        Return a single link in the document.
        """
        name = operation_info.get('operationId')
        title = operation_info.get('summary')
        description = operation_info.get('description')

        if name is None:
            name = _simple_slugify(title)
            if not name:
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
            fields += [Field(name='body', location='body', schema=schema)]

        return Link(
            name=name,
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
        schema_defs = {}
        paths = self.get_paths(document, schema_defs=schema_defs)
        openapi = OPEN_API.validate({
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

        if schema_defs:
            openapi['components'] = {'schemas': schema_defs}

        if not document.url:
            openapi.pop('servers')

        kwargs = {
            'ensure_ascii': False,
            'indent': 4,
            'separators': (',', ': ')
        }
        return json.dumps(openapi, **kwargs).encode('utf-8')

    def get_paths(self, document, schema_defs=None):
        paths = dict_type()

        for link, name, sections in document.walk_links():
            path = urlparse(link.url).path
            operation_id = link.name
            tag = sections[0].name if sections else None
            method = link.method.lower()

            if path not in paths:
                paths[path] = {}
            paths[path][method] = self.get_operation(link, operation_id, tag=tag, schema_defs=schema_defs)

        return paths

    def get_operation(self, link, operation_id, tag=None, schema_defs=None):
        operation = {
            'operationId': operation_id
        }
        if link.title:
            operation['summary'] = link.title
        if link.description:
            operation['description'] = link.description
        if tag:
            operation['tags'] = [tag]
        if link.get_path_fields() or link.get_query_fields():
            operation['parameters'] = [
                self.get_parameter(field, schema_defs) for field in
                link.get_path_fields() + link.get_query_fields()
            ]
        if link.get_body_field():
            schema = link.get_body_field().schema
            if schema is None:
                content_info = {}
            else:
                content_info = {
                    'schema': JSONSchemaCodec().encode_to_data_structure(
                        schema,
                        schema_defs,
                        '#/components/schemas/'
                    )
                }

            operation['requestBody'] = {
                'content': {
                    link.encoding: content_info
                }
            }
        if link.response is not None:
            operation['responses'] = {
                str(link.response.status_code): {
                    'description': '',
                    'content': {
                        link.response.encoding: {
                            'schema': JSONSchemaCodec().encode_to_data_structure(
                                link.response.schema,
                                schema_defs,
                                '#/components/schemas/'
                            )
                        }
                    }
                }
            }
        return operation

    def get_parameter(self, field, schema_defs=None):
        parameter = {
            'name': field.name,
            'in': field.location
        }
        if field.required:
            parameter['required'] = True
        if field.description:
            parameter['description'] = field.description
        if field.schema:
            parameter['schema'] = JSONSchemaCodec().encode_to_data_structure(
                field.schema,
                schema_defs,
                '#/components/schemas/'
            )
        return parameter

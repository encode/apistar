import re
from urllib.parse import urljoin

from apistar import validators
from apistar.compat import dict_type
from apistar.document import Document, Field, Link, Section
from apistar.schemas.jsonschema import JSON_SCHEMA, JSONSchema

SCHEMA_REF = validators.Object(
    properties={'$ref': validators.String(pattern='^#/definitiions/')}
)
RESPONSE_REF = validators.Object(
    properties={'$ref': validators.String(pattern='^#/responses/')}
)

SWAGGER = validators.Object(
    def_name='Swagger',
    title='Swagger',
    properties=[
        ('swagger', validators.String()),
        ('info', validators.Ref('Info')),
        ('paths', validators.Ref('Paths')),
        ('host', validators.String()),
        ('basePath', validators.String()),
        ('schemes', validators.Array(items=validators.String())),
        ('consumes', validators.Array(items=validators.String())),
        ('produces', validators.Array(items=validators.String())),
        ('definitions', validators.Object(additional_properties=validators.Any())),
        ('parameters', validators.Object(additional_properties=validators.Ref('Parameters'))),
        ('responses', validators.Object(additional_properties=validators.Ref('Responses'))),
        ('securityDefinitions', validators.Object(additional_properties=validators.Ref('SecurityScheme'))),
        ('security', validators.Array(items=validators.Ref('SecurityRequirement'))),
        ('tags', validators.Array(items=validators.Ref('Tag'))),
        ('externalDocs', validators.Ref('ExternalDocumentation')),
    ],
    pattern_properties={
        '^x-': validators.Any(),
    },
    additional_properties=False,
    required=['swagger', 'info', 'paths'],
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
                ('consumes', validators.Array(items=validators.String())),
                ('produces', validators.Array(items=validators.String())),
                ('parameters', validators.Array(items=validators.Ref('Parameter'))),  # TODO: | ReferenceObject
                ('responses', validators.Ref('Responses')),
                ('schemes', validators.Array(items=validators.String())),
                ('deprecated', validators.Boolean()),
                ('security', validators.Array(validators.Ref('SecurityRequirement'))),
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
                ('in', validators.String(enum=['query', 'header', 'path', 'formData', 'body'])),
                ('description', validators.String(format='textarea')),
                ('required', validators.Boolean()),
                # in: "body"
                ('schema', JSON_SCHEMA | SCHEMA_REF),
                # in: "query"|"header"|"path"|"formData"
                ('type', validators.String()),
                ('format', validators.String()),
                ('allowEmptyValue', validators.Boolean()),
                ('items', JSON_SCHEMA),  # TODO: Should actually be a restricted subset
                ('collectionFormat', validators.String(enum=['csv', 'ssv', 'tsv', 'pipes', 'multi'])),
                ('default', validators.Any()),
                ('maximum', validators.Number()),
                ('exclusiveMaximum', validators.Boolean()),
                ('minimum', validators.Number()),
                ('exclusiveMinimum', validators.Boolean()),
                ('maxLength', validators.Integer()),
                ('minLength', validators.Integer()),
                ('pattern', validators.String()),
                ('maxItems', validators.Integer()),
                ('minItems', validators.Integer()),
                ('uniqueItems', validators.Boolean()),
                ('enum', validators.Array(items=validators.Any())),
                ('multipleOf', validators.Integer()),
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
                ('type', validators.String(enum=['basic', 'apiKey', 'oauth2'])),
                ('description', validators.String(format='textarea')),
                ('name', validators.String()),
                ('in', validators.String(enum=['query', 'header'])),
                ('flow', validators.String(enum=['implicit', 'password', 'application', 'accessCode'])),
                ('authorizationUrl', validators.String(format="url")),
                ('tokenUrl', validators.String(format="url")),
                ('scopes', validators.Ref('Scopes')),
            ],
            pattern_properties={
                '^x-': validators.Any(),
            },
            additional_properties=False,
            required=['type']
        ),
        'Scopes': validators.Object(
            pattern_properties={
                '^x-': validators.Any(),
            },
            additional_properties=validators.String(),
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


def _simple_slugify(text):
    if text is None:
        return None
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    text = re.sub(r'[_]+', '_', text)
    return text.strip('_')


class Swagger:
    def load(self, data):
        title = lookup(data, ['info', 'title'])
        description = lookup(data, ['info', 'description'])
        version = lookup(data, ['info', 'version'])
        host = lookup(data, ['host'])
        path = lookup(data, ['basePath'], '/')
        scheme = lookup(data, ['schemes', 0], 'https')
        base_url = None
        if host:
            base_url = '%s://%s%s' % (scheme, host, path)
        schema_definitions = self.get_schema_definitions(data)
        content = self.get_content(data, base_url, schema_definitions)
        return Document(title=title, description=description, version=version, url=base_url, content=content)

    def get_schema_definitions(self, data):
        definitions = {}
        schemas = lookup(data, ['components', 'schemas'], {})
        for key, value in schemas.items():
            definitions[key] = JSONSchema().decode_from_data_structure(value)
            definitions[key].def_name = key
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

        # Parameters are taken both from the path info, and from the operation.
        parameters = path_info.get('parameters', [])
        parameters += operation_info.get('parameters', [])

        fields = [
            self.get_field(parameter, schema_definitions)
            for parameter in parameters
        ]

        default_encoding = None
        if any([field.location == 'body' for field in fields]):
            default_encoding = 'application/json'
        elif any([field.location == 'formData' for field in fields]):
            default_encoding = 'application/x-www-form-urlencoded'
            form_fields = [field for field in fields if field.location == 'formData']
            body_field = Field(
                name='body',
                location='body',
                schema=validators.Object(
                    properties={
                        field.name: validators.Any() if field.schema is None else field.schema
                        for field in form_fields
                    },
                    required=[field.name for field in form_fields if field.required]
                )
            )
            fields = [field for field in fields if field.location != 'formData']
            fields.append(body_field)

        encoding = lookup(operation_info, ['consumes', 0], default_encoding)

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
                ref = schema['$ref'][len('#/definitions/'):]
                schema = schema_definitions.get(ref)
            else:
                schema = JSONSchema().decode_from_data_structure(schema)

        return Field(
            name=name,
            location=location,
            description=description,
            required=required,
            schema=schema,
            example=example
        )

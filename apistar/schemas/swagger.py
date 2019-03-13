import re
from urllib.parse import urljoin

import typesystem
from apistar.document import Document, Field, Link, Section
from apistar.schemas.jsonschema import JSON_SCHEMA

SCHEMA_REF = typesystem.Object(
    properties={"$ref": typesystem.String(pattern="^#/definitiions/")}
)
RESPONSE_REF = typesystem.Object(
    properties={"$ref": typesystem.String(pattern="^#/responses/")}
)

definitions = typesystem.SchemaDefinitions()

SWAGGER = typesystem.Object(
    title="Swagger",
    properties={
        "swagger": typesystem.String(),
        "info": typesystem.Reference("Info", definitions=definitions),
        "paths": typesystem.Reference("Paths", definitions=definitions),
        "host": typesystem.String(),
        "basePath": typesystem.String(pattern="^/"),
        "schemes": typesystem.Array(items=typesystem.Choice(choices=["http", "https", "ws", "wss"])),
        "consumes": typesystem.Array(items=typesystem.String()),
        "produces": typesystem.Array(items=typesystem.String()),
        "definitions": typesystem.Object(additional_properties=typesystem.Any()),
        "parameters": typesystem.Object(
            additional_properties=typesystem.Reference(
                "Parameters", definitions=definitions
            )
        ),
        "responses": typesystem.Object(
            additional_properties=typesystem.Reference(
                "Responses", definitions=definitions
            )
        ),
        "securityDefinitions": typesystem.Object(
            additional_properties=typesystem.Reference(
                "SecurityScheme", definitions=definitions
            )
        ),
        "security": typesystem.Array(
            items=typesystem.Reference("SecurityRequirement", definitions=definitions)
        ),
        "tags": typesystem.Array(
            items=typesystem.Reference("Tag", definitions=definitions)
        ),
        "externalDocs": typesystem.Reference(
            "ExternalDocumentation", definitions=definitions
        ),
    },
    pattern_properties={"^x-": typesystem.Any()},
    additional_properties=False,
    required=["swagger", "info", "paths"],
)

definitions["Info"] = typesystem.Object(
    properties={
        "title": typesystem.String(allow_blank=True),
        "description": typesystem.Text(allow_blank=True),
        "termsOfService": typesystem.String(format="url"),
        "contact": typesystem.Reference("Contact", definitions=definitions),
        "license": typesystem.Reference("License", definitions=definitions),
        "version": typesystem.String(allow_blank=True),
    },
    pattern_properties={"^x-": typesystem.Any()},
    additional_properties=False,
    required=["title", "version"],
)

definitions["Contact"] = typesystem.Object(
    properties={
        "name": typesystem.String(allow_blank=True),
        "url": typesystem.String(format="url"),
        "email": typesystem.String(format="email"),
    },
    pattern_properties={"^x-": typesystem.Any()},
    additional_properties=False,
)

definitions["License"] = typesystem.Object(
    properties={"name": typesystem.String(), "url": typesystem.String(format="url")},
    required=["name"],
    pattern_properties={"^x-": typesystem.Any()},
    additional_properties=False,
)

definitions["Paths"] = typesystem.Object(
    pattern_properties={
        "^/": typesystem.Reference("Path", definitions=definitions),
        "^x-": typesystem.Any(),
    },
    additional_properties=False,
)

definitions["Path"] = typesystem.Object(
    properties={
        "summary": typesystem.String(allow_blank=True),
        "description": typesystem.Text(allow_blank=True),
        "get": typesystem.Reference("Operation", definitions=definitions),
        "put": typesystem.Reference("Operation", definitions=definitions),
        "post": typesystem.Reference("Operation", definitions=definitions),
        "delete": typesystem.Reference("Operation", definitions=definitions),
        "options": typesystem.Reference("Operation", definitions=definitions),
        "head": typesystem.Reference("Operation", definitions=definitions),
        "patch": typesystem.Reference("Operation", definitions=definitions),
        "trace": typesystem.Reference("Operation", definitions=definitions),
        "parameters": typesystem.Array(
            items=typesystem.Reference("Parameter", definitions=definitions)
        ),  # TODO: | ReferenceObject
    },
    pattern_properties={"^x-": typesystem.Any()},
    additional_properties=False,
)

definitions["Operation"] = typesystem.Object(
    properties={
        "tags": typesystem.Array(items=typesystem.String()),
        "summary": typesystem.String(allow_blank=True),
        "description": typesystem.Text(allow_blank=True),
        "externalDocs": typesystem.Reference(
            "ExternalDocumentation", definitions=definitions
        ),
        "operationId": typesystem.String(),
        "consumes": typesystem.Array(items=typesystem.String()),
        "produces": typesystem.Array(items=typesystem.String()),
        "parameters": typesystem.Array(
            items=typesystem.Reference("Parameter", definitions=definitions)
        ),  # TODO: | ReferenceObject
        "responses": typesystem.Reference("Responses", definitions=definitions),
        "schemes": typesystem.Array(items=typesystem.Choice(choices=["http", "https", "ws", "wss"])),
        "deprecated": typesystem.Boolean(),
        "security": typesystem.Array(
            typesystem.Reference("SecurityRequirement", definitions=definitions)
        ),
    },
    pattern_properties={"^x-": typesystem.Any()},
    additional_properties=False,
)

definitions["ExternalDocumentation"] = typesystem.Object(
    properties={
        "description": typesystem.Text(),
        "url": typesystem.String(format="url"),
    },
    pattern_properties={"^x-": typesystem.Any()},
    additional_properties=False,
    required=["url"],
)

definitions["Parameter"] = typesystem.Object(
    properties={
        "name": typesystem.String(),
        "in": typesystem.Choice(
            choices=["query", "header", "path", "formData", "body"]
        ),
        "description": typesystem.Text(),
        "required": typesystem.Boolean(),
        # in: "body"
        "schema": JSON_SCHEMA | SCHEMA_REF,
        # in: "query"|"header"|"path"|"formData"
        "type": typesystem.Choice(choices=["string", "number", "integer", "boolean", "array", "file"]),
        "format": typesystem.String(allow_blank=True),
        "allowEmptyValue": typesystem.Boolean(),
        "items": JSON_SCHEMA,  # TODO: Should actually be a restricted subset
        "collectionFormat": typesystem.Choice(
            choices=["csv", "ssv", "tsv", "pipes", "multi"]
        ),
        "default": typesystem.Any(),
        "maximum": typesystem.Number(),
        "exclusiveMaximum": typesystem.Boolean(),
        "minimum": typesystem.Number(),
        "exclusiveMinimum": typesystem.Boolean(),
        "maxLength": typesystem.Integer(),
        "minLength": typesystem.Integer(),
        "pattern": typesystem.String(allow_blank=True),
        "maxItems": typesystem.Integer(),
        "minItems": typesystem.Integer(),
        "uniqueItems": typesystem.Boolean(),
        "enum": typesystem.Array(items=typesystem.Any()),
        "multipleOf": typesystem.Integer(),
    },
    pattern_properties={"^x-": typesystem.Any()},
    additional_properties=False,
    required=["name", "in"],
)

definitions["RequestBody"] = typesystem.Object(
    properties={
        "description": typesystem.String(allow_blank=True),
        "content": typesystem.Object(
            additional_properties=typesystem.Reference(
                "MediaType", definitions=definitions
            )
        ),
        "required": typesystem.Boolean(),
    },
    pattern_properties={"^x-": typesystem.Any()},
    additional_properties=False,
)

definitions["Responses"] = typesystem.Object(
    properties={
        "default": typesystem.Reference("Response", definitions=definitions)
        | RESPONSE_REF
    },
    pattern_properties={
        "^([1-5][0-9][0-9]|[1-5]XX)$": typesystem.Reference(
            "Response", definitions=definitions
        )
        | RESPONSE_REF,
        "^x-": typesystem.Any(),
    },
    additional_properties=False,
)

definitions["Response"] = typesystem.Object(
    properties={
        "description": typesystem.String(allow_blank=True),
        "content": typesystem.Object(
            additional_properties=typesystem.Reference(
                "MediaType", definitions=definitions
            )
        ),
        "headers": typesystem.Object(
            additional_properties=typesystem.Reference(
                "Header", definitions=definitions
            )
        ),
        # TODO: Header | ReferenceObject
        # TODO: links
    },
    pattern_properties={"^x-": typesystem.Any()},
    additional_properties=False,
)

definitions["MediaType"] = typesystem.Object(
    properties={
        "schema": JSON_SCHEMA | SCHEMA_REF,
        "example": typesystem.Any(),
        # TODO 'examples', 'encoding'
    },
    pattern_properties={"^x-": typesystem.Any()},
    additional_properties=False,
)

definitions["Header"] = typesystem.Object(
    properties={
        "description": typesystem.Text(),
        "type": typesystem.Choice(choices=["string", "number", "integer", "boolean", "array", "file"]),
        "format": typesystem.String(allow_blank=True),
        "items": JSON_SCHEMA,  # TODO: Should actually be a restricted subset
        "collectionFormat": typesystem.Choice(
            choices=["csv", "ssv", "tsv", "pipes", "multi"]
        ),
        "default": typesystem.Any(),
        "maximum": typesystem.Number(),
        "exclusiveMaximum": typesystem.Boolean(),
        "minimum": typesystem.Number(),
        "exclusiveMinimum": typesystem.Boolean(),
        "maxLength": typesystem.Integer(),
        "minLength": typesystem.Integer(),
        "pattern": typesystem.String(allow_blank=True),
        "maxItems": typesystem.Integer(),
        "minItems": typesystem.Integer(),
        "uniqueItems": typesystem.Boolean(),
        "enum": typesystem.Array(items=typesystem.Any()),
        "multipleOf": typesystem.Integer(),
    },
    pattern_properties={"^x-": typesystem.Any()},
    additional_properties=False,
)

definitions["Tag"] = typesystem.Object(
    properties={
        "name": typesystem.String(),
        "description": typesystem.Text(allow_blank=True),
        "externalDocs": typesystem.Reference(
            "ExternalDocumentation", definitions=definitions
        ),
    },
    pattern_properties={"^x-": typesystem.Any()},
    additional_properties=False,
    required=["name"],
)

definitions["SecurityRequirement"] = typesystem.Object(
    additional_properties=typesystem.Array(items=typesystem.String())
)

definitions["SecurityScheme"] = typesystem.Object(
    properties={
        "type": typesystem.Choice(choices=["basic", "apiKey", "oauth2"]),
        "description": typesystem.Text(allow_blank=True),
        "name": typesystem.String(),
        "in": typesystem.Choice(choices=["query", "header"]),
        "flow": typesystem.Choice(
            choices=["implicit", "password", "application", "accessCode"]
        ),
        "authorizationUrl": typesystem.String(format="url"),
        "tokenUrl": typesystem.String(format="url"),
        "scopes": typesystem.Reference("Scopes", definitions=definitions),
    },
    pattern_properties={"^x-": typesystem.Any()},
    additional_properties=False,
    required=["type"],
)

definitions["Scopes"] = typesystem.Object(
    pattern_properties={"^x-": typesystem.Any()},
    additional_properties=typesystem.String(),
)


METHODS = ["get", "put", "post", "delete", "options", "head", "patch", "trace"]


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
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"[_]+", "_", text)
    return text.strip("_")


class Swagger:
    def load(self, data):
        title = lookup(data, ["info", "title"])
        description = lookup(data, ["info", "description"])
        version = lookup(data, ["info", "version"])
        host = lookup(data, ["host"])
        path = lookup(data, ["basePath"], "/")
        scheme = lookup(data, ["schemes", 0], "https")
        base_url = None
        if host:
            base_url = "%s://%s%s" % (scheme, host, path)
        schema_definitions = self.get_schema_definitions(data)
        content = self.get_content(data, base_url, schema_definitions)
        return Document(
            title=title,
            description=description,
            version=version,
            url=base_url,
            content=content,
        )

    def get_schema_definitions(self, data):
        definitions = typesystem.SchemaDefinitions()
        schemas = lookup(data, ["components", "schemas"], {})
        for key, value in schemas.items():
            ref = f"#/components/schemas/{key}"
            definitions[ref] = typesystem.from_json_schema(
                value, definitions=definitions
            )
        return definitions

    def get_content(self, data, base_url, schema_definitions):
        """
        Return all the links in the document, layed out by tag and operationId.
        """
        links_by_tag = {}
        links = []

        for path, path_info in data.get("paths", {}).items():
            operations = {key: path_info[key] for key in path_info if key in METHODS}
            for operation, operation_info in operations.items():
                tag = lookup(operation_info, ["tags", 0])
                link = self.get_link(
                    base_url,
                    path,
                    path_info,
                    operation,
                    operation_info,
                    schema_definitions,
                )
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

    def get_link(
        self, base_url, path, path_info, operation, operation_info, schema_definitions
    ):
        """
        Return a single link in the document.
        """
        name = operation_info.get("operationId")
        title = operation_info.get("summary")
        description = operation_info.get("description")

        if name is None:
            name = _simple_slugify(title)
            if not name:
                return None

        # Parameters are taken both from the path info, and from the operation.
        parameters = path_info.get("parameters", [])
        parameters += operation_info.get("parameters", [])

        fields = [
            self.get_field(parameter, schema_definitions) for parameter in parameters
        ]

        default_encoding = None
        if any([field.location == "body" for field in fields]):
            default_encoding = "application/json"
        elif any([field.location == "formData" for field in fields]):
            default_encoding = "application/x-www-form-urlencoded"
            form_fields = [field for field in fields if field.location == "formData"]
            body_field = Field(
                name="body",
                location="body",
                schema=typesystem.Object(
                    properties={
                        field.name: typesystem.Any()
                        if field.schema is None
                        else field.schema
                        for field in form_fields
                    },
                    required=[field.name for field in form_fields if field.required],
                ),
            )
            fields = [field for field in fields if field.location != "formData"]
            fields.append(body_field)

        encoding = lookup(operation_info, ["consumes", 0], default_encoding)

        return Link(
            name=name,
            url=urljoin(base_url, path),
            method=operation,
            title=title,
            description=description,
            fields=fields,
            encoding=encoding,
        )

    def get_field(self, parameter, schema_definitions):
        """
        Return a single field in a link.
        """
        name = parameter.get("name")
        location = parameter.get("in")
        description = parameter.get("description")
        required = parameter.get("required", False)
        schema = parameter.get("schema")
        example = parameter.get("example")

        if schema is not None:
            if "$ref" in schema:
                ref = schema["$ref"]
                schema = schema_definitions.get(ref)
            else:
                schema = typesystem.from_json_schema(
                    schema, definitions=schema_definitions
                )

        return Field(
            name=name,
            location=location,
            description=description,
            required=required,
            schema=schema,
            example=example,
        )

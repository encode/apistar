import inspect

from coreapi import Document, Field, Link
from uritemplate import URITemplate

from apistar import schema
from apistar.app import App
from apistar.routing import primitive_types, schema_types


class APISchema(Document):
    @classmethod
    def build(cls, app: App):
        content = {}

        for (path, method, view) in app.routes:
            view_signature = inspect.signature(view)
            uritemplate = URITemplate(path)
            name = view.__name__

            fields = []
            for param in view_signature.parameters.values():

                if param.annotation is inspect.Signature.empty:
                    annotated_type = str
                else:
                    annotated_type = param.annotation

                location = None
                required = False
                if param.name in uritemplate.variable_names:
                    location = 'path'
                    required = True
                elif (annotated_type in primitive_types) or issubclass(annotated_type, schema_types):
                    if method in ('POST', 'PUT', 'PATCH'):
                        if issubclass(annotated_type, schema.Object):
                            location = 'body'
                            required = True
                        else:
                            location = 'form'
                    else:
                        location = 'query'

                if location is not None:
                    field = Field(name=param.name, location=location, required=required)
                    fields.append(field)

            link = Link(url=path, action=method, fields=fields)
            content[name] = link

        return cls(content=content)

import click
from coreapi.utils import get_installed_codecs

from apistar import schema

codecs = {
    name: codec for name, codec in get_installed_codecs().items()
    if '+' in codec.media_type
}


class Format(schema.String):
    description = 'The format for the API Schema output.'
    default = 'corejson'
    choices = list(codecs.keys())


def schema(format: Format) -> None:  # pragma: nocover
    """
    Output an API Schema.
    """
    from apistar.main import get_current_app
    from apistar.apischema import APISchema
    app = get_current_app()
    schema = APISchema.build(app)
    codec = codecs[format]
    output = codec.encode(schema)
    click.echo(output)

import click

from apistar import exceptions
from apistar.codecs import OpenAPICodec


@click.command()
@click.argument('schema_file', type=click.File('rb'))
def validate(schema_file):
    content = schema_file.read()
    codec = OpenAPICodec()
    try:
        codec.decode(content)
    except (exceptions.ParseError, exceptions.ValidationError) as exc:
        click.echo(exc)
        click.echo('[FAILED]')
        return
    click.echo('[OK]')


if __name__ == '__main__':
    validate()

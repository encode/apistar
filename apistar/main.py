import os
import shutil

import click
import jinja2

import apistar
from apistar import codecs
from apistar.exceptions import ParseError, ValidationError
from apistar.formatters import get_errors


def static_url(filename):
    return filename


@click.group()
def main():
    pass


@click.command()
@click.argument('schema', type=click.File('rb'))
def validate(schema):
    # encoder = JSONErrorEncoder(errors={'123': 'Yikes', 'abc': {1: 'Nope'}}, indent=4)
    # click.echo(encoder.encode({'123': '...', 'abc': ['...', '...', '...']}))
    # return

    codec = codecs.OpenAPICodec()
    content = schema.read()
    if content.decode().strip() and content.decode().strip()[0] in '{[':
        content_type = 'json'
    else:
        content_type = 'yaml'

    try:
        codec.decode(content)
    except (ParseError, ValidationError) as exc:
        errors = get_errors(content, exc, content_type)
        lines = content.splitlines()
        for error in reversed(errors):
            error_str = ' ' * (error.start.column - 1)
            error_str += '^ '
            error_str += error.message
            error_str = click.style(error_str, fg='red')
            lines.insert(error.start.row, error_str)
        for line in lines:
            click.echo(line)

        click.echo()
        if isinstance(exc, ParseError) and content_type == 'json':
            click.echo(click.style('✘', fg='red') + ' Invalid JSON.')
        elif isinstance(exc, ParseError) and content_type == 'yaml':
            click.echo(click.style('✘', fg='red') + ' Invalid YAML.')
        else:
            click.echo(click.style('✘', fg='red') + ' Invalid OpenAPI 3 document.')

    else:
        click.echo(click.style('✓', fg='green') + ' Valid OpenAPI 3 document.')


@click.command()
@click.argument('schema', type=click.File('rb'))
def docs(schema):
    codec = codecs.OpenAPICodec()
    content = schema.read()
    document = codec.decode(content)

    loader = jinja2.PrefixLoader({
        'apistar': jinja2.PackageLoader('apistar', 'templates')
    })
    env = jinja2.Environment(autoescape=True, loader=loader)

    template = env.get_template('apistar/docs/index.html')
    code_style = None  # pygments_css('emacs')
    output_text = template.render(
        document=document,
        langs=['javascript', 'python'],
        code_style=code_style,
        static_url=static_url
    )

    directory = 'site'
    output_path = os.path.join(directory, 'index.html')
    if not os.path.exists(directory):
        os.makedirs(directory)
    output_file = open(output_path, 'w')
    output_file.write(output_text)
    output_file.close()

    static_dir = os.path.join(os.path.dirname(apistar.__file__), 'static')
    shutil.copytree(static_dir, os.path.join(directory, 'apistar'))

    click.echo('Documentation built at %s' % output_path)


main.add_command(docs)
main.add_command(validate)

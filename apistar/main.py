import os
import shutil

import click
import jinja2

import apistar
from apistar import codecs
from apistar.exceptions import ParseError, ValidationError
from apistar.formatters.json_errors import json_errors
from apistar.formatters.yaml_errors import yaml_errors


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
    is_json = content.decode().strip() and content.decode().strip()[0] in '{['
    try:
        codec.decode(content)
    except ParseError as exc:
        if is_json:
            click.echo(click.style('✘', fg='red') + ' Invalid JSON.')
        else:
            click.echo(click.style('✘', fg='red') + ' Invalid YAML.')
        click.echo()
        if exc.pos is None:
            click.echo(exc)
        else:
            valid_lines = content.splitlines()[:exc.lineno-1]
            invalid_line = content.splitlines()[exc.lineno-1]
            remaining_lines = content.splitlines()[exc.lineno:]

            click.echo(b'\n'.join(valid_lines))
            click.echo(invalid_line)
            click.echo(' ' * (exc.colno - 1), nl=False)
            click.echo(click.style('^ ' + exc.short_message, fg='red'))
            click.echo(b'\n'.join(remaining_lines))
    except ValidationError as exc:
        click.echo(click.style('✘', fg='red') + ' Invalid OpenAPI 3 document.')
        click.echo()
        if is_json:
            click.echo(json_errors(exc.value, exc.detail))
        else:
            click.echo(yaml_errors(exc.value, exc.detail))
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

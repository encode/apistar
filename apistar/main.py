import os
import shutil
import sys

import click
import http.server
import jinja2
import socketserver

import apistar
from apistar.exceptions import ParseError, ValidationError
from apistar.schemas import OpenAPI, Swagger
from apistar.validate import validate as apistar_validate


def static_url(filename):
    return filename


@click.group()
def main():
    pass


def _base_format_from_filename(filename, default=None):
    base, extension = os.path.splitext(filename)
    return {
        '.json': 'json',
        '.yml': 'yaml',
        '.yaml': 'yaml'
    }.get(extension, default)


def _echo_error(exc, content, verbose=False):
    if verbose:
        # Verbose output style.
        lines = content.splitlines()
        for message in reversed(exc.messages):
            error_str = ' ' * (message.position.column_no - 1)
            error_str += '^ '
            error_str += message.text
            error_str = click.style(error_str, fg='red')
            lines.insert(message.position.line_no, error_str)
        for line in lines:
            click.echo(line)

        click.echo()
    else:
        # Compact output style.
        for message in exc.messages:
            pos = message.position
            if message.code == 'required':
                index = message.index[:-1]
            else:
                index = message.index
            if index:
                fmt = '* %s (At %s, line %d, column %d.)'
                output = fmt % (message.text, index, pos.line_no, pos.column_no)
                click.echo(output)
            else:
                fmt = '* %s (At line %d, column %d.)'
                output = fmt % (message.text, pos.line_no, pos.column_no)
                click.echo(output)

    click.echo(click.style('✘ ', fg='red') + exc.summary)


def _copy_tree(src, dst, verbose=False):
    if not os.path.exists(dst):
        os.makedirs(dst)

    for name in os.listdir(src):
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        if os.path.isdir(srcname):
            _copy_tree(srcname, dstname, verbose=verbose)
        else:
            if verbose:
                click.echo(dstname)
            shutil.copy2(srcname, dstname)


FORMAT_SCHEMA_CHOICES = click.Choice(['openapi', 'swagger'])
FORMAT_ALL_CHOICES = click.Choice(['json', 'yaml', 'config', 'jsonschema', 'openapi', 'swagger'])
BASE_FORMAT_CHOICES = click.Choice(['json', 'yaml'])
THEME_CHOICES = click.Choice(['apistar', 'redoc', 'swaggerui'])


@click.command()
@click.argument('schema', type=click.File('rb'))
@click.option('--format', type=FORMAT_ALL_CHOICES, required=True)
@click.option('--base-format', type=BASE_FORMAT_CHOICES, default=None)
@click.option('--verbose', '-v', is_flag=True, default=False)
def validate(schema, format, base_format, verbose):
    content = schema.read()
    if base_format is None:
        base_format = _base_format_from_filename(schema.name)

    try:
        value = apistar_validate(content, format=format, base_format=base_format)
    except (ParseError, ValidationError) as exc:
        _echo_error(exc, content, verbose=verbose)
        sys.exit(1)

    success_summary = {
        'json': 'Valid JSON',
        'yaml': 'Valid YAML',
        'config': 'Valid APIStar config.',
        'jsonschema': 'Valid JSONSchema document.',
        'openapi': 'Valid OpenAPI schema.',
        'swagger': 'Valid Swagger schema.',
    }[format]
    click.echo(click.style('✓ ', fg='green') + success_summary)


@click.command()
@click.argument('schema', type=click.File('rb'))
@click.option('--format', type=FORMAT_SCHEMA_CHOICES, required=True)
@click.option('--base-format', type=BASE_FORMAT_CHOICES, default=None)
@click.option('--output-dir', type=click.Path(), default='build')
@click.option('--theme', type=THEME_CHOICES, default='apistar')
@click.option('--serve', is_flag=True, default=False)
@click.option('--verbose', '-v', is_flag=True, default=False)
def docs(schema, format, base_format, output_dir, theme, serve, verbose):
    content = schema.read()
    if base_format is None:
        base_format = _base_format_from_filename(schema.name, default="yaml")

    try:
        value = apistar_validate(content, format=format, base_format=base_format)
    except (ParseError, ValidationError) as exc:
        _echo_error(exc, content, verbose=verbose)
        sys.exit(1)

    decoder = {
        'openapi': OpenAPI,
        'swagger': Swagger
    }[format]
    document = decoder().load(value)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Write 'index.html' to the docs.
    loader = jinja2.PrefixLoader({
        theme: jinja2.PackageLoader('apistar', os.path.join('themes', theme, 'templates'))
    })
    env = jinja2.Environment(autoescape=True, loader=loader)

    template = env.get_template(os.path.join(theme, 'index.html'))
    code_style = None  # pygments_css('emacs')
    schema_filename = 'schema.%s' % base_format
    output_text = template.render(
        document=document,
        langs=['javascript', 'python'],
        code_style=code_style,
        static_url=static_url,
        schema_url='/' + schema_filename
    )

    output_path = os.path.join(output_dir, 'index.html')
    if verbose:
        click.echo(output_path)
    output_file = open(output_path, 'w')
    output_file.write(output_text)
    output_file.close()

    # Write 'schema.{json|yaml}' to the docs.
    schema_path = os.path.join(output_dir, schema_filename)
    if verbose:
        click.echo(schema_path)
    shutil.copy2(schema.name, schema_path)

    # Write static files to the docs.
    package_dir = os.path.dirname(apistar.__file__)
    static_dir = os.path.join(package_dir, 'themes', theme, 'static')
    _copy_tree(static_dir, output_dir, verbose=verbose)

    # All done.
    if serve:
        os.chdir(output_dir)
        addr = ("", 8000)
        handler = http.server.SimpleHTTPRequestHandler
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(addr, handler) as httpd:
            msg = 'Documentation available at "http://127.0.0.1:8000/" (Ctrl+C to quit)'
            click.echo(click.style('✓ ', fg='green') + msg)
            httpd.serve_forever()
    else:
        msg = 'Documentation built at "%s".'
        click.echo(click.style('✓ ', fg='green') + (msg % output_path))


main.add_command(docs)
main.add_command(validate)

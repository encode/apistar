import http.server
import json
import os
import shutil
import socketserver
import sys

import click

import apistar
from apistar.client import Client
from apistar.client.debug import DebugSession
from apistar.exceptions import (
    ClientError, ErrorResponse, ParseError, ValidationError
)


def _encoding_from_filename(filename):
    base, extension = os.path.splitext(filename)
    return {
        '.json': 'json',
        '.yml': 'yaml',
        '.yaml': 'yaml'
    }.get(extension)


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


def _load_config(options, verbose=False):
    if not os.path.exists('apistar.yml'):
        # If the config file is not used, then --path is required.
        if options['schema']['path'] is None:
            raise click.UsageError('Missing option "--path".')
        config = options

    else:
        with open('apistar.yml', 'rb') as config_file:
            content = config_file.read()

        try:
            config = apistar.validate(content, format='config', encoding="yaml")
        except (ParseError, ValidationError) as exc:
            click.echo('Errors in configuration file "apistar.yml":')
            _echo_error(exc, content, verbose=verbose)
            sys.exit(1)

        # Anything passed in 'options' should override the config file.
        # Ensure all values are populated with 'None' if unset.
        for section in options.keys():
            config.setdefault(section, {})
            for key, value in options[section].items():
                config[section].setdefault(key, None)
                if value is not None:
                    config[section][key] = value

    path = config['schema']['path']
    if not os.path.exists(path):
        raise click.UsageError('Schema file "%s" not found.' % path)

    if config['schema']['encoding'] is None:
        config['schema']['encoding'] = _encoding_from_filename(path)

    return config


FORMAT_SCHEMA_CHOICES = click.Choice(['openapi', 'swagger'])
FORMAT_ALL_CHOICES = click.Choice(['config', 'jsonschema', 'openapi', 'swagger'])
ENCODING_CHOICES = click.Choice(['json', 'yaml'])
THEME_CHOICES = click.Choice(['apistar', 'redoc', 'swaggerui'])


@click.group()
def cli():
    pass


@click.command()
@click.option('--path', type=click.Path(exists=True, dir_okay=False))
@click.option('--format', type=FORMAT_ALL_CHOICES)
@click.option('--encoding', type=ENCODING_CHOICES)
@click.option('--verbose', '-v', is_flag=True, default=False)
def validate(path, format, encoding, verbose):
    options = {
        'schema': {
            'path': path,
            'format': format,
            'encoding': encoding
        }
    }
    config = _load_config(options, verbose=verbose)

    path = config['schema']['path']
    format = config['schema']['format']
    encoding = config['schema']['encoding']

    with open(path, 'rb') as schema_file:
        content = schema_file.read()

    try:
        apistar.validate(content, format=format, encoding=encoding)
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
@click.option('--path', type=click.Path(exists=True, dir_okay=False))
@click.option('--format', type=FORMAT_SCHEMA_CHOICES)
@click.option('--encoding', type=ENCODING_CHOICES)
@click.option('--output-dir', type=click.Path())
@click.option('--theme', type=THEME_CHOICES)
@click.option('--serve', is_flag=True, default=False)
@click.option('--verbose', '-v', is_flag=True, default=False)
def docs(path, format, encoding, output_dir, theme, serve, verbose):
    options = {
        'schema': {
            'path': path,
            'format': format,
            'encoding': encoding,
        },
        'docs': {
            'output_dir': output_dir,
            'theme': theme,
        }
    }
    config = _load_config(options, verbose=verbose)

    path = config['schema']['path']
    format = config['schema']['format']
    encoding = config['schema']['encoding']
    output_dir = config['docs']['output_dir']
    theme = config['docs']['theme']

    if output_dir is None:
        output_dir = 'build'
    if theme is None:
        theme = 'apistar'

    schema_filename = os.path.basename(path)
    schema_url = '/' + schema_filename
    with open(path, 'rb') as schema_file:
        content = schema_file.read()

    try:
        index_html = apistar.docs(content, format=format, encoding=encoding, schema_url=schema_url)
    except (ParseError, ValidationError) as exc:
        _echo_error(exc, content, verbose=verbose)
        sys.exit(1)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Write 'index.html' to the docs.
    output_path = os.path.join(output_dir, 'index.html')
    if verbose:
        click.echo(output_path)
    output_file = open(output_path, 'w')
    output_file.write(index_html)
    output_file.close()

    # Write schema file to the docs.
    schema_path = os.path.join(output_dir, schema_filename)
    if verbose:
        click.echo(schema_path)
    shutil.copy2(path, schema_path)

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


@click.command()
@click.argument('operation')
@click.argument('params', nargs=-1)
@click.option('--path', type=click.Path(exists=True, dir_okay=False))
@click.option('--format', type=FORMAT_SCHEMA_CHOICES)
@click.option('--encoding', type=ENCODING_CHOICES)
@click.option('--verbose', '-v', is_flag=True, default=False)
@click.pass_context
def request(ctx, operation, params, path, format, encoding, verbose):
    options = {
        'schema': {
            'path': path,
            'format': format,
            'encoding': encoding
        }
    }
    config = _load_config(options, verbose=verbose)

    path = config['schema']['path']
    format = config['schema']['format']
    encoding = config['schema']['encoding']

    with open(path, 'rb') as schema_file:
        schema = schema_file.read()

    params = [param.partition('=') for param in params]
    params = dict([(key, value) for key, sep, value in params])

    session = ctx.obj

    if verbose:
        session = DebugSession(session)

    try:
        client = Client(schema, format=format, encoding=encoding, session=session)
    except (ParseError, ValidationError) as exc:
        _echo_error(exc, schema, verbose=verbose)
        sys.exit(1)

    try:
        result = client.request(operation, **params)
    except ClientError as exc:
        for message in exc.messages:
            if message.code == 'invalid_property':
                text = '* Invalid parameter "%s".' % exc.index[0]
            elif message.code == 'required':
                text = '* Missing required parameter "%s".' % exc.index[0]
            else:
                text = exc.text
            click.echo(text)
        click.echo(click.style('✘ ', fg='red') + 'Client error')
        sys.exit(1)
    except ErrorResponse as exc:
        click.echo(json.dumps(exc.content, indent=4))
        click.echo(click.style('✘ ', fg='red') + exc.title)
        sys.exit(1)
    click.echo(json.dumps(result, indent=4))


cli.add_command(docs)
cli.add_command(validate)
cli.add_command(request)

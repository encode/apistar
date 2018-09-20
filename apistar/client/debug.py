"""
This module provides a `DebugSession` requests session class, that echos
requests and responses to the console.

We use this for the `apistar request --verbose` console command.
"""
from urllib.parse import urlparse

import click
from requests.adapters import HTTPAdapter
from requests.sessions import Session


def expand_args(fmt, args):
    if args:
        return fmt % args
    return fmt


def debug_request(request):
    def request_echo(fmt, *args):
        click.echo(click.style('> ', fg='blue') + expand_args(fmt, args))

    request_echo(click.style('%s %s HTTP/1.1', bold=True), request.method, request.path_url)

    if 'host' not in request.headers:
        request_echo('Host: %s', urlparse(request.url).netloc)

    for key, value in sorted(request.headers.items()):
        request_echo('%s: %s', key.title(), value)

    if request.body:
        body_text = request.body
        if isinstance(body_text, bytes):
            body_text = body_text.decode('utf-8')
        request_echo('')
        for line in body_text.splitlines():
            request_echo(line)


def debug_response(response):
    def success_echo(fmt, *args):
        prompt = click.style('< ', fg='green')
        click.echo(prompt + expand_args(fmt, args))

    def failure_echo(fmt, *args):
        prompt = click.style('< ', fg='red')
        click.echo(prompt + expand_args(fmt, args))

    def info_echo(fmt, *args):
        prompt = click.style('< ', fg='yellow')
        click.echo(prompt + expand_args(fmt, args))

    response_class = ('%s' % response.status_code)[0] + 'xx'
    if response_class == '2xx':
        response_echo = success_echo
    elif response_class in ('4xx', '5xx'):
        response_echo = failure_echo
    else:
        response_echo = info_echo

    response_echo(click.style('%d %s', bold=True), response.status_code, response.reason)
    for key, value in sorted(response.headers.items()):
        response_echo('%s: %s', key.title(), value)
    if response.content:
        response_echo('')
        for line in response.text.splitlines():
            response_echo(line)

    click.echo()


class DebugAdapter(HTTPAdapter):
    def __init__(self, wrapped_session=None):
        self.session = Session() if wrapped_session is None else wrapped_session
        super().__init__()

    def send(self, request, **kwargs):
        debug_request(request)
        response = self.session.send(request, **kwargs)
        debug_response(response)
        return response


def DebugSession(wrapped_session=None):
    session = Session()
    session.mount('https://', DebugAdapter(wrapped_session))
    session.mount('http://', DebugAdapter(wrapped_session))
    return session

import argparse
import inspect
import re
import typing

from apistar import exceptions
from apistar.interfaces import CommandLineClient
from apistar.types import CommandConfig, HandlerLookup


def main(usage):
    return usage


class ArgParseCommandLineClient(CommandLineClient):
    def __init__(self,
                 commands: CommandConfig) -> None:
        parser = MainArgumentParser(description='API Star', add_help=False)
        parser.set_defaults(handler=main)
        parser.add_argument('--help', action=HelpAction)

        for name, handler in commands:
            description, parameter_descriptions = self.get_descriptions(handler)

            command = parser.add_command(name, description=description, add_help=False)
            command.set_defaults(handler=handler)
            command.add_argument('--help', action=HelpAction)

            parameters = inspect.signature(handler).parameters
            for param_name, param in parameters.items():
                description = parameter_descriptions.get(param_name, '')
                annotation = param.annotation
                if annotation is inspect.Parameter.empty:
                    annotation = str

                if issubclass(annotation, (str, int, float, bool)):
                    name = param_name.replace('_', '-')
                    default = param.default
                    if default is inspect.Parameter.empty:
                        command.add_positional(
                            param_name,
                            metavar=name.upper(),
                            help=description,
                            type=annotation
                        )
                    elif default is False:
                        command.add_option(
                            '--%s' % name,
                            help=description,
                            dest=param_name,
                            action='store_true',
                            default=default
                        )
                    elif default is True:
                        command.add_option(
                            '--no-%s' % name,
                            help=description,
                            dest=param_name,
                            action='store_false',
                            default=default
                        )
                    else:
                        command.add_option(
                            '--%s' % name,
                            help=description,
                            dest=param_name,
                            type=annotation,
                            action='store',
                            default=default
                        )

        self._parser = parser

    def get_descriptions(self, handler: typing.Callable):
        doc = getattr(handler, '__doc__')

        if doc is None:
            return ('', {})

        lines = [line.strip() for line in doc.strip().splitlines()]
        if '' in lines:
            description = '\n'.join(lines[:lines.index('')])
        else:
            description = '\n'.join(lines)

        param_names = inspect.signature(handler).parameters.keys()
        param_docs = {}
        for param_name in param_names:
            match = re.search('^\W*' + param_name + '\W*(.*)$', doc, re.MULTILINE)
            if match:
                param_docs[param_name] = match.groups()[0]
            else:
                param_docs[param_name] = ''

        return (description, param_docs)

    def parse(self,
              args: typing.Sequence[str]) -> HandlerLookup:
        kwargs = vars(self._parser.parse_args(args))
        handler = kwargs.pop('handler')
        if handler is main:
            kwargs['usage'] = self._parser.format_usage()
        return handler, kwargs


class HelpAction(argparse.Action):
    def __init__(self,
                 option_strings,
                 dest=argparse.SUPPRESS,
                 default=argparse.SUPPRESS,
                 help=None):
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help='Show this message and exit.'
        )

    def __call__(self, parser, namespace, values, option_string=None):
        message = parser.format_help()
        raise exceptions.CommandLineExit(message)


class MainArgumentParser(argparse.ArgumentParser):
    prog = ''
    description = ''

    def __init__(self, description: str, add_help: bool) -> None:
        super().__init__(description=description, add_help=add_help)
        self.commands = []  # type: typing.List[typing.Tuple[str, str]]
        self.subparsers = self.add_subparsers(parser_class=CommandArgumentParser)

    def add_command(self, name: str, **kwargs):
        first = name
        second = kwargs.get('description', '')
        self.commands.append((first, second))
        return self.subparsers.add_parser(name, **kwargs)

    def error(self, message: str) -> None:
        raise exceptions.CommandLineError(message)

    def format_usage(self) -> str:
        message = 'Usage: {prog} COMMAND [OPTIONS] [ARGS]...'
        return message.format(prog=self.prog)

    def format_description(self) -> str:
        if not self.description:  # pragma: nocover
            return ''
        return '\n\n  %s' % self.description

    def format_options(self) -> str:
        options = [('--help', 'Show this message and exit.')]
        return '\n\nOptions:\n' + format_dl(options)

    def format_commands(self) -> str:
        if not self.commands:  # pragma: nocover
            return ''
        return '\n\nCommands:\n' + format_dl(self.commands)

    def format_help(self) -> str:
        return ''.join([
            self.format_usage(),
            self.format_description(),
            self.format_options(),
            self.format_commands()
        ])


class CommandArgumentParser(argparse.ArgumentParser):
    prog = ''
    description = ''

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.positionals = []  # type: typing.List[typing.Tuple[str, str]]
        self.options = []  # type: typing.List[typing.Tuple[str, str]]

    def add_positional(self, name: str, **kwargs) -> None:
        first = name
        second = kwargs.get('help', '')
        self.positionals.append((first, second))
        self.add_argument(name, **kwargs)

    def add_option(self, name: str, **kwargs) -> None:
        if 'type' in kwargs:
            first = name + ' ' + self.format_type(kwargs['type'])
        else:
            first = name
        second = kwargs.get('help', '')
        self.options.append((first, second))
        self.add_argument(name, **kwargs)

    def error(self, message: str) -> None:
        raise exceptions.CommandLineError(message)

    def format_type(self, cls: type) -> str:
        if issubclass(cls, int):
            return 'INTEGER'
        elif issubclass(cls, float):
            return 'FLOAT'
        return 'TEXT'

    def format_usage(self) -> str:
        message = 'Usage: {prog}'
        for name, description in self.positionals:
            message += ' ' + name.upper()
        message += ' [OPTIONS]'
        return message.format(prog=self.prog)

    def format_description(self) -> str:
        if not self.description:
            return ''
        return '\n\n  %s' % self.description

    def format_options(self) -> str:
        options = [('--help', 'Show this message and exit.')] + self.options
        return '\n\nOptions:\n' + format_dl(options)

    def format_help(self) -> str:
        return ''.join([
            self.format_usage(),
            self.format_description(),
            self.format_options()
        ])


def format_dl(rows) -> str:
    spacing = max(len(first) for first, second in rows)
    return '\n'.join([
        '  %-*s  %s' % (spacing, first, second)
        for first, second in rows
    ])

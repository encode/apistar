import argparse
import inspect
import typing

from apistar import exceptions
from apistar.interfaces import CommandConfig, CommandLineClient, HandlerLookup


def main(usage):
    return usage


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise exceptions.CommandLineError(message)


class ArgParseCommandLineClient(CommandLineClient):
    def __init__(self,
                 commands: CommandConfig) -> None:
        parser = ArgumentParser()
        parser.set_defaults(handler=main)
        subparsers = parser.add_subparsers(title='Commands', metavar='[COMMAND]')

        for name, handler in commands:
            subparser = subparsers.add_parser(name, help='')
            subparser.set_defaults(handler=handler)

            parameters = inspect.signature(handler).parameters
            for param_name, param in parameters.items():
                subparser.add_argument(param_name)

        self._parser = parser

    def parse(self,
              args: typing.Sequence[str]) -> HandlerLookup:
        kwargs = vars(self._parser.parse_args(args))
        handler = kwargs.pop('handler')
        if handler is main:
            kwargs['usage'] = self._parser.format_usage()
        return handler, kwargs

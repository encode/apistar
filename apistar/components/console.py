"""
Implementations of the `Console` interface.

Currently these are trivial cases. Smarter implementations might perform
behavior such as handling ANSI colors, as the 'click' package does.
"""
from apistar.interfaces import Console


class PrintConsole(Console):
    """
    Implementation of the standard console behavior.
    """
    def echo(self, message=''):  # pragma: nocover
        print(message)


class BufferConsole(Console):
    """
    An implementation of buffered console behavior,
    useful for testing the output of command line handlers.
    """
    def __init__(self):
        self.buffer = ''

    def echo(self, message=''):
        self.buffer += message
        if not message.endswith('\n'):
            self.buffer += '\n'

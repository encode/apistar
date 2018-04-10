import pytest

from apistar import Command, exceptions
from apistar.frameworks.cli import CliApp
from apistar.frameworks.wsgi import WSGIApp
from apistar.types import AppLoader
from apistar.commands.run import import_app


def no_args():
    return 'abc'


def required_args(a, b):
    """
    Returns the values for a and b.
    """
    return 'a=%s, b=%s' % (a, b)


def default_args(a=True, b=False, c: int=None, d: float=None):
    """
    Returns the values for a, b, c, and d, which have default values.

    Args:
      a: A flag which may be turned [on|off].
      b: A flag which may be turned [on|off].
      c: A parameter.
      d: A parameter.
    """
    return 'a=%s, b=%s, c=%s, d=%s' % (a, b, c, d)


def app_loader_args(a: AppLoader=import_app):
    """
    Returns the values for a.

    Args:
      a: A parameter.
    """
    return 'a=%s' % type(a)


commands = [
    Command('no_args', no_args),
    Command('required_args', required_args),
    Command('default_args', default_args),
    Command('app_loader_args', app_loader_args)
]
app = CliApp(commands=commands)


wsgi_app = WSGIApp()
wsgi_app.__call__ = lambda *args, **kwargs: print('ok.')


def _get_help_lines(content):
    """
    Return the help text split into lines, but replacing the
    progname part of the usage line.
    """
    lines = content.splitlines()
    lines[0] = 'Usage: <progname> ' + ' '.join(lines[0].split()[2:])
    return lines


def test_main():
    ret = app.main([], standalone_mode=False)
    assert ret.startswith('Usage:')


def test_help():
    ret = app.main(['--help'], standalone_mode=False)
    assert _get_help_lines(ret) == [
        "Usage: <progname> COMMAND [OPTIONS] [ARGS]...",
        "",
        "  API Star",
        "",
        "Options:",
        "  --help  Show this message and exit.",
        "",
        "Commands:",
        "  new              Create a new project in TARGET_DIR.",
        "  run              Run the development server.",
        "  schema           Generate an API schema.",
        "  test             Run the test suite.",
        "  no_args          ",
        "  required_args    Returns the values for a and b.",
        "  default_args     Returns the values for a, b, c, and d, which have default values.",
        "  app_loader_args  Returns the values for a.",
    ]


def test_no_args_subcommand_help():
    ret = app.main(['no_args', '--help'], standalone_mode=False)
    lines = _get_help_lines(ret)
    assert lines == [
        "Usage: <progname> no_args [OPTIONS]",
        "",
        "Options:",
        "  --help  Show this message and exit."
    ]


def test_required_args_subcommand_help():
    ret = app.main(['required_args', '--help'], standalone_mode=False)
    lines = _get_help_lines(ret)
    assert lines == [
        "Usage: <progname> required_args A B [OPTIONS]",
        "",
        "  Returns the values for a and b.",
        "",
        "Options:",
        "  --help  Show this message and exit."
    ]


def test_default_args_subcommand_help():
    ret = app.main(['default_args', '--help'], standalone_mode=False)
    lines = _get_help_lines(ret)
    assert lines == [
        "Usage: <progname> default_args [OPTIONS]",
        "",
        "  Returns the values for a, b, c, and d, which have default values.",
        "",
        "Options:",
        "  --help       Show this message and exit.",
        "  --no-a       A flag which may be turned [on|off].",
        "  --b          A flag which may be turned [on|off].",
        "  --c INTEGER  A parameter.",
        "  --d FLOAT    A parameter."
    ]


def test_app_loader_subcommand_help():
    ret = app.main(['app_loader_args', '--help'], standalone_mode=False)
    lines = _get_help_lines(ret)
    assert lines == [
        "Usage: <progname> app_loader_args A [OPTIONS]",
        "",
        "  Returns the values for a.",
        "",
        "Options:",
        "  --help  Show this message and exit.",
    ]


def test_noargs():
    ret = app.main(['no_args'], standalone_mode=False)
    assert ret == 'abc'


def test_required_args():
    ret = app.main(['required_args', '1', '2'], standalone_mode=False)
    assert ret == 'a=1, b=2'


def test_default_args():
    ret = app.main(['default_args'], standalone_mode=False)
    assert ret == 'a=True, b=False, c=None, d=None'

    ret = app.main(['default_args', '--b'], standalone_mode=False)
    assert ret == 'a=True, b=True, c=None, d=None'

    ret = app.main(['default_args', '--no-a'], standalone_mode=False)
    assert ret == 'a=False, b=False, c=None, d=None'

    ret = app.main(['default_args', '--c', '123'], standalone_mode=False)
    assert ret == 'a=True, b=False, c=123, d=None'

    ret = app.main(['default_args', '--d', '123'], standalone_mode=False)
    assert ret == 'a=True, b=False, c=None, d=123.0'


def test_app_loader_args():
    ret = app.main(['app_loader_args', 'tests.test_commandline:wsgi_app'], standalone_mode=False)
    assert ret == "a=<class 'apistar.frameworks.wsgi.WSGIApp'>"


def test_unknown_command():
    with pytest.raises(exceptions.CommandLineError):
        app.main(['unknown'], standalone_mode=False)


def test_missing_required_args():
    with pytest.raises(exceptions.CommandLineError):
        app.main(['required_args', '1'], standalone_mode=False)


def test_invalid_args():
    with pytest.raises(exceptions.CommandLineError):
        app.main(['default_args', '--c', 'abc'], standalone_mode=False)

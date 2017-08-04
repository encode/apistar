import pytest

from apistar import App, Command, exceptions


def no_args():
    return 'abc'


def required_args(a, b):
    return 'a=%s, b=%s' % (a, b)


def default_args(a=True, b=False, c: int=None):
    return 'a=%s, b=%s, c=%s' % (a, b, c)


commands = [
    Command('no_args', no_args),
    Command('default_args', default_args),
    Command('required_args', required_args)
]
app = App(commands=commands)


def test_main():
    ret = app.main([], standalone_mode=False)
    assert ret.startswith('usage:')


def test_noargs():
    ret = app.main(['no_args'], standalone_mode=False)
    assert ret == 'abc'


def test_required_args():
    ret = app.main(['required_args', '1', '2'], standalone_mode=False)
    assert ret == 'a=1, b=2'


def test_default_args():
    ret = app.main(['default_args'], standalone_mode=False)
    assert ret == 'a=True, b=False, c=None'

    ret = app.main(['default_args', '--b'], standalone_mode=False)
    assert ret == 'a=True, b=True, c=None'

    ret = app.main(['default_args', '--no-a'], standalone_mode=False)
    assert ret == 'a=False, b=False, c=None'

    ret = app.main(['default_args', '--c', '123'], standalone_mode=False)
    assert ret == 'a=True, b=False, c=123'


def test_missing_required_args():
    with pytest.raises(exceptions.CommandLineError):
        app.main(['required_args', '1'], standalone_mode=False)

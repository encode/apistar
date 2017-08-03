import pytest

from apistar import App, Command, exceptions


def no_args():
    return 'abc'


def required_args(a, b):
    return 'a=%s, b=%s' % (a, b)


commands = [
    Command('no_args', no_args),
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


def test_missing_required_args():
    with pytest.raises(exceptions.CommandLineError):
        app.main(['required_args', '1'], standalone_mode=False)

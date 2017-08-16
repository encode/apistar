import pytest

from apistar import environment, exceptions, typesystem


class Env(environment.Environment):
    properties = {
        'DEBUG': typesystem.boolean(default=False),
        'DATABASE_URL': typesystem.string()
    }


def test_valid_env():
    env = Env({
        'DEBUG': 'False',
        'DATABASE_URL': 'sqlite:///test.db'
    })
    assert env['DEBUG'] is False
    assert env['DATABASE_URL'] == 'sqlite:///test.db'


def test_env_missing_optional():
    env = Env({
        'DATABASE_URL': 'sqlite:///test.db'
    })
    assert env['DEBUG'] is False
    assert env['DATABASE_URL'] == 'sqlite:///test.db'


def test_env_missing_required():
    with pytest.raises(exceptions.ConfigurationError):
        Env({
            'DEBUG': 'False'
        })


def test_os_environ():
    """
    The usual invokation is to call the class with no arguments.
    In this case `os.environ` should be used as the instantiation value.
    We inject a mock environment here to test this case.
    """
    class TestEnv(Env):
        _os_environ = {
            'DEBUG': 'FALSE',
            'DATABASE_URL': 'sqlite:///test.db'
        }

    env = TestEnv()
    assert env['DEBUG'] is False
    assert env['DATABASE_URL'] == 'sqlite:///test.db'

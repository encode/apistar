import os
import pytest
import tempfile

from apistar import environment, exceptions, schema
from apistar.main import setup_environ


class Env(environment.Environment):
    properties = {
        'TESTCASE_DEBUG': schema.Boolean(default=False),
        'TESTCASE_DATABASE_URL': schema.String
    }
    required = ['TESTCASE_DATABASE_URL']


def test_explicit_env():
    env = Env({
        'TESTCASE_DEBUG': 'False',
        'TESTCASE_DATABASE_URL': 'sqlite:///test.db'
    })
    assert env['TESTCASE_DEBUG'] is False
    assert env['TESTCASE_DATABASE_URL'] == 'sqlite:///test.db'


def test_missing_optional():
    env = Env({
        'TESTCASE_DATABASE_URL': 'sqlite:///test.db'
    })
    assert env['TESTCASE_DEBUG'] is False


def test_missing_required():
    with pytest.raises(exceptions.ConfigurationError):
        env = Env({})


def test_implicit_env():
    os.environ['TESTCASE_DEBUG'] = 'FALSE'
    os.environ['TESTCASE_DATABASE_URL'] = 'sqlite:///test.db'

    env = Env()
    assert env['TESTCASE_DEBUG'] is False
    assert env['TESTCASE_DATABASE_URL'] == 'sqlite:///test.db'


def test_env_file():
    with tempfile.NamedTemporaryFile('w') as env_file:
        env_file.write('TESTCASE_DEBUG=False\n')
        env_file.write('TESTCASE_DATABASE_URL=sqlite:///test.db\n')
        env_file.flush()
        setup_environ(env_file.name)
        env = Env()
        assert env['TESTCASE_DEBUG'] is False
        assert env['TESTCASE_DATABASE_URL'] == 'sqlite:///test.db'

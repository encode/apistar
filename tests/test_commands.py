import os

import click

from apistar import __version__, exceptions
from apistar.app import App
from apistar.main import setup_pythonpath
from apistar.test import CommandLineRunner

app = App()
runner = CommandLineRunner(app)


def test_help_flag():
    result = runner.invoke([])
    assert '--help' in result.output
    assert '--version' in result.output
    assert 'new' in result.output
    assert 'run' in result.output
    assert 'test' in result.output
    assert result.exit_code == 0


def test_version_flag():
    result = runner.invoke(['--version'])
    assert __version__ in result.output
    assert result.exit_code == 0


def test_custom_command():
    def custom(var):
        click.echo(var)

    app = App(commands=[custom])
    runner = CommandLineRunner(app)

    result = runner.invoke([])
    assert 'custom' in result.output

    result = runner.invoke(['custom', '123'])
    assert result.output == '123\n'
    assert result.exit_code == 0


def test_custom_command_with_int_arguments():
    def add(a: int, b: int):
        click.echo(str(a + b))

    app = App(commands=[add])
    runner = CommandLineRunner(app)

    result = runner.invoke([])
    assert 'add' in result.output

    result = runner.invoke(['add', '1', '2'])
    assert result.output == '3\n'
    assert result.exit_code == 0


def test_new():
    with runner.isolated_filesystem():
        runner.invoke(['new', 'myproject', '--layout', 'minimal'])
        assert os.path.exists('myproject')
        assert os.path.exists(os.path.join('myproject', 'app.py'))
        assert os.path.exists(os.path.join('myproject', 'tests.py'))


def test_do_not_overwrite_existing_project():
    with runner.isolated_filesystem():
        result = runner.invoke(['new', 'myproject', '--layout', 'minimal'])
        assert result.exit_code == 0
        result = runner.invoke(['new', 'myproject', '--layout', 'minimal'])
        assert result.exit_code != 0


def test_testsuite_minimal():
    with runner.isolated_filesystem():
        runner.invoke(['new', 'myproject', '--layout', 'minimal'])
        os.chdir('myproject')
        setup_pythonpath()
        result = runner.invoke(['test'])
        assert '2 passed' in result.output
        assert result.exit_code == 0


def test_testsuite_standard():
    with runner.isolated_filesystem():
        runner.invoke(['new', 'myproject'])
        os.chdir('myproject')
        setup_pythonpath()
        result = runner.invoke(['test'])
        assert '2 passed' in result.output
        assert result.exit_code == 0

        # Add a failing test case.
        failing_test_module = os.path.join('tests', 'test_failure.py')
        with open(failing_test_module, 'w') as test_module:
            test_module.write('def test_failure():\n    raise Exception()\n')
        result = runner.invoke(['test'])
        assert '1 failed, 2 passed' in result.output
        assert result.exit_code != 0


def test_testsuite_missing_tests_module():
    with runner.isolated_filesystem():
        runner.invoke(['new', 'myproject', '--layout', 'minimal'])
        os.chdir('myproject')
        setup_pythonpath()
        os.remove('tests.py')
        result = runner.invoke(['test'])
        assert isinstance(result.exception, exceptions.ConfigurationError)
        assert result.exit_code != 0


def test_missing_app_module():
    with runner.isolated_filesystem():
        runner.invoke(['new', 'myproject', '--layout', 'minimal'])
        os.chdir('myproject')
        setup_pythonpath()
        os.remove('app.py')
        result = runner.invoke(['run'])
        assert isinstance(result.exception, exceptions.ConfigurationError)
        assert result.exit_code != 0


def test_misconfigured_app_module():
    with runner.isolated_filesystem():
        runner.invoke(['new', 'myproject', '--layout', 'minimal'])
        os.chdir('myproject')
        setup_pythonpath()
        with open('app.py', 'w') as app_module:
            app_module.write('123\n')
        result = runner.invoke(['run'])
        assert isinstance(result.exception, exceptions.ConfigurationError)
        assert result.exit_code != 0


def test_schema():
    with runner.isolated_filesystem():
        runner.invoke(['new', '.', '--layout', 'minimal'])
        result = runner.invoke(['schema'])
        assert result.exit_code == 0
        assert result.output == (
            '{"_type":"document","_meta":{"url":"/docs/schema"},'
            '"welcome":{"_type":"link","url":"/","action":"GET",'
            '"fields":[{"name":"name","location":"query","schema'
            '":{"_type":"string","title":"","description":""}}]}}\n'
        )

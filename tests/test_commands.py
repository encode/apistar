from apistar import __version__
from apistar.app import App
from apistar.main import setup_pythonpath
from apistar.test import CommandLineRunner
import os


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


def test_new():
    with runner.isolated_filesystem():
        runner.invoke(['new', 'myproject', '--template', 'minimal'])
        assert os.path.exists('myproject')
        assert os.path.exists(os.path.join('myproject', 'app.py'))
        assert os.path.exists(os.path.join('myproject', 'tests.py'))


def test_testsuite_minimal():
    with runner.isolated_filesystem():
        runner.invoke(['new', 'myproject', '--template', 'minimal'])
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

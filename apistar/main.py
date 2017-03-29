"""
The `apistar` command line client.
"""
import importlib.util
import os
import sys


sys.dont_write_bytecode = True


def get_current_app():
    app_path = os.path.join(os.getcwd(), 'app.py')
    if os.path.exists(app_path):
        spec = importlib.util.spec_from_file_location("app", app_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        app = module.app
    else:
        from apistar import App
        app = App()
    return app


def setup_environ():
    env_path = os.path.join(os.getcwd(), '.env')
    if os.path.exists(env_path):
        for line in open(env_path, 'r'):
            variable, sep, value = line.partition('=')
            variable = variable.strip()
            value = value.strip()
            if variable:
                os.environ[variable] = value


def setup_pythonpath():
    cwd = os.getcwd()
    sys.path.insert(0, cwd)


def main():  # pragma: no cover
    setup_pythonpath()
    setup_environ()
    app = get_current_app()
    app.click()


if __name__ == '__main__':  # pragma: no cover
    main()

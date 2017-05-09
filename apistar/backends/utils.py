import importlib


default_db_backend = 'apistar.backends.sqlalchemy.SQLAlchemy'


def db_backend_loader(settings):
    database_settings = settings.get('DATABASE', {})
    backend_name = database_settings.get('BACKEND', default_db_backend)

    parts = backend_name.split('.')
    class_name = parts.pop()
    module_name = '.'.join(parts)
    module = importlib.import_module(module_name)
    backend = getattr(module, class_name)

    return backend

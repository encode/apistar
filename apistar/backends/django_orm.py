import contextlib
import sys
import typing

import django
from django.apps import apps
from django.conf import settings as django_settings
from django.core.management import call_command
from django.db import connections, transaction

from apistar import Command, Component, Settings


class DjangoORM(object):
    def __init__(self, settings: Settings) -> None:
        config = {
            'INSTALLED_APPS': settings.get('INSTALLED_APPS', []),
            'DATABASES': settings.get('DATABASES', {}),
            'AUTH_USER_MODEL': settings.get('AUTH_USER_MODEL', 'auth.User')
        }
        django_settings.configure(**config)
        django.setup()
        self.models = {
            model.__name__: model
            for model in apps.get_models()
        }


class Session(object):
    def __init__(self, orm: DjangoORM) -> None:
        for name, model in orm.models.items():
            setattr(self, name, model)


@contextlib.contextmanager
def get_session(backend: DjangoORM) -> typing.Generator[Session, None, None]:
    """
    Create a new context-managed database session, which automatically
    handles atomic rollback or commit behavior.

    Args:
      backend: The configured database backend.
    """
    for conn in connections.all():
        conn.queries_log.clear()
        conn.close_if_unusable_or_obsolete()

    atomic = transaction.Atomic(using=None, savepoint=True)

    atomic.__enter__()
    try:
        yield Session(backend)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        atomic.__exit__(exc_type, exc_value, exc_traceback)
        raise
    exc_type, exc_value, exc_traceback = (None, None, None)
    atomic.__exit__(exc_type, exc_value, exc_traceback)


def flush():  # pragma: nocover
    call_command('flush', '--no-input')


def makemigrations():  # pragma: nocover
    call_command('makemigrations')


def migrate():
    call_command('migrate')


def showmigrations():  # pragma: nocover
    call_command('showmigrations')


components = [
    Component(DjangoORM),
    Component(Session, init=get_session, preload=False)
]

commands = [
    Command('flush', flush),
    Command('makemigrations', makemigrations),
    Command('migrate', migrate),
    Command('showmigrations', showmigrations)
]

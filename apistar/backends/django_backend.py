from django import setup
from django.apps import apps
from django.conf import settings as django_settings
from django.core.management import call_command

from apistar.settings import Settings


class DjangoBackend(object):

    preload = True
    _loaded = False

    @classmethod
    def build(cls, settings: Settings) -> "DjangoBackend":
        if not cls._loaded:
            django_settings.configure(**settings)
            setup()
            cls._loaded = True
        dj = cls()
        for model in apps.get_models():
            setattr(dj, model.__name__, model)
        return dj

    def makemigrations(self) -> None:
        call_command('makemigrations')

    def migrate(self) -> None:
        call_command('migrate')

    def showmigrations(self) -> None:
        call_command('showmigrations')

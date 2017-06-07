from django import setup
from django.apps import apps
from django.conf import settings as django_settings
from django.core.management import call_command

from apistar.settings import Settings


class DjangoBackend(object):

    preload = True
    _loaded = False

    @classmethod
    def build(cls, settings: Settings):
        if not cls._loaded and not django_settings.configured:
            django_settings.configure(INSTALLED_APPS=settings.get('INSTALLED_APPS'),
                                      DATABASES=settings.get('DATABASES'))
            setup()
            cls._loaded = True
        dj = cls()
        for model in apps.get_models():
            setattr(dj, model.__name__, model)
        return dj

    def makemigrations(self):
        call_command('makemigrations')

    def migrate(self):
        call_command('migrate')

    def showmigrations(self):
        call_command('showmigrations')

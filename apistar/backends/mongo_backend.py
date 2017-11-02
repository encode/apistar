import contextlib
import typing

from bson.objectid import ObjectId
from pymongo import MongoClient

from apistar import Command, Component, Settings

registered_collections = []


def collection(cls):
    """
    Decorator to register apistar custom Objects as mongodb collections
    """

    registered_collections.append({
        'collection': cls.__name__.lower(),
        'class': cls,
    })

    def __init__(self, *args, **kwargs):
        if len(args) == 1 and not kwargs and isinstance(args[0], dict):
            id = args[0].pop('_id', None)
        else:
            id = kwargs.pop('_id', None)

        if id:
            self['_id'] = id

        super(cls, self).__init__(*args, **kwargs)

    def __setitem__(self, index, value):
        if index == '_id':
            if type(value) is ObjectId:
                self.id = value
                value = str(value)
            else:
                self.id = ObjectId(value)

        super(cls, self).__setitem__(index, value)

    cls.__init__ = __init__
    cls.__setitem__ = __setitem__

    return cls


class MongoBackend(object):
    def __init__(self, settings: Settings) -> None:
        """
        Configure MongoDB database backend.

        Args:
            settings: The application settings dictionary.
        """

        self.config = settings.get('DATABASE', {})
        self.url = self.config.get('URL', '')
        self.database_name = self.config.get('NAME', '')
        self.client = None

    def connect(self) -> None:
        self.client = MongoClient(self.url)

    def close(self) -> None:
        if self.client:
            self.client.close()

        self.client = None

    def drop_database(self) -> None:
        self.connect()
        self.client.drop_database(self.database_name)
        self.close()


class Session(object):
    """
    Class responsible to hold a mongodb session instance
    """
    def __init__(self, backend: MongoBackend) -> None:
        self.db = backend.client[backend.database_name]
        for model in registered_collections:
            setattr(self, model['collection'], self.db[model['collection']])


@contextlib.contextmanager
def get_session(backend: MongoBackend) -> typing.Generator[Session,
                                                           None, None]:
    """
    Create a new context-managed database session for mongodb
    """
    backend.connect()

    yield Session(backend)

    backend.close()


def drop_database(backend: MongoBackend) -> None:
    """
    Drop the mongodb database from defined at settings
    """
    backend.drop_database()


components = [
    Component(MongoBackend),
    Component(Session, init=get_session, preload=False),
]

commands = [
    Command('drop_database', drop_database),
]

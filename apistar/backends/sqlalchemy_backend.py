import contextlib
import typing

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from apistar import Command, Component, Settings


class SQLAlchemyBackend(object):
    def __init__(self, settings: Settings) -> None:
        """
        Configure a new database backend.

        Args:
          settings: The application settings dictionary.
        """
        database_config = settings['DATABASE']
        url = database_config['URL']
        metadata = database_config['METADATA']

        kwargs = {}
        if url.startswith('postgresql'):  # pragma: nocover
            kwargs['pool_size'] = database_config.get('POOL_SIZE', 5)

        self.metadata = metadata
        self.engine = create_engine(url, **kwargs)
        self.Session = sessionmaker(bind=self.engine)


@contextlib.contextmanager
def get_session(backend: SQLAlchemyBackend) -> typing.Generator[Session, None, None]:
    """
    Create a new context-managed database session, which automatically
    handles rollback or commit behavior.

    Args:
      backend: The configured database backend.
    """
    session = backend.Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def create_tables(backend: SQLAlchemyBackend):
    """
    Create all database tables.

    Args:
      backend: The configured database backend.
    """
    backend.metadata.create_all(backend.engine)


def drop_tables(backend: SQLAlchemyBackend):
    """
    Drop all database tables.

    Args:
      backend: The configured database backend.
    """
    backend.metadata.drop_all(backend.engine)


components = [
    Component(SQLAlchemyBackend),
    Component(Session, init=get_session, preload=False)
]

commands = [
    Command('create_tables', create_tables),
    Command('drop_tables', drop_tables)
]

# from apistar.settings import Settings
from apistar import commands
from apistar.backends.base import BaseDatabaseBackend


class SQLAlchemy(BaseDatabaseBackend):
    __slots__ = ('engine', 'session_class', 'metadata', )

    preload_key = 'sql_alchemy'
    commands = [commands.create_tables, ]

    def __init__(self, engine, session_class, metadata=None):
        self.engine = engine
        self.session_class = session_class
        self.metadata = metadata

    @classmethod
    def build(cls, settings):
        config = settings['DATABASE']
        url = config['URL']
        metadata = config['METADATA']

        kwargs = {}
        if url.startswith('postgresql'):  # pragma: no cover
            kwargs['pool_size'] = config.get('POOL_SIZE', 5)

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(url, **kwargs)
        session_class = sessionmaker(bind=engine)
        return cls(engine, session_class, metadata)

    def create_tables(self):
        self.metadata.create_all(self.engine)

    def drop_tables(self):
        self.metadata.drop_all(self.engine)

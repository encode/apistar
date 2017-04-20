from typing import Dict
from apistar.exceptions import ConfigurationError


class DBBackend(object):
    __slots__ = ('engine', 'session_class', 'metadata')

    def __init__(self, engine, session_class, metadata=None):
        self.engine = engine
        self.session_class = session_class
        self.metadata = metadata

    @classmethod
    def build(cls, db_config: Dict):
        if db_config and db_config.get('TYPE') == "SQLALCHEMY":
            if 'URL' in db_config:

                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker

                engine = create_engine(
                    db_config['URL'],
                    echo=True,
                    echo_pool=True,
                    pool_size=db_config.get('POOL_SIZE', 5)
                )
                session_class = sessionmaker(bind=engine)

                db_backend = cls(
                    engine=engine,
                    session_class=session_class,
                    metadata=db_config.get('METADATA')
                )

                return db_backend
        return None

    def create_tables(self):
        if not self.metadata:
            raise ConfigurationError("App must be configured with Metadata class to create tables")
        self.metadata.create_all(self.engine)

from typing import Dict


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

                try:
                    engine = create_engine(
                        db_config['URL'],
                        pool_size=db_config.get('POOL_SIZE', 5)
                    )
                except TypeError:
                    # pool size doesnt work with SQLite
                    engine = create_engine(db_config['URL'])

                session_class = sessionmaker(bind=engine)

                db_backend = cls(
                    engine=engine,
                    session_class=session_class,
                    metadata=db_config.get('METADATA')
                )

                return db_backend
        return None

    def create_tables(self):
        self.metadata.create_all(self.engine)

    def drop_tables(self):
        self.metadata.drop_all(self.engine)

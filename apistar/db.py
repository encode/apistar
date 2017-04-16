from typing import Dict


class DBBackend(object):
    __slots__ = ('engine', 'session_class')

    def __init__(self, engine, session_class):
        self.engine = engine
        self.session_class = session_class

    @classmethod
    def build(cls, db_engine_config: Dict):
        if db_engine_config and db_engine_config.get('TYPE') == "SQLALCHEMY":
            if 'DB_URL' in db_engine_config:

                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker

                engine = create_engine(
                    db_engine_config['DB_URL'],
                    echo=True,
                    echo_pool=True,
                    pool_size=db_engine_config.get('DB_POOL_SIZE', 5)
                )
                session_class = sessionmaker(bind=engine)

                db_backend = cls(engine=engine, session_class=session_class)

                if 'METADATA' in db_engine_config:
                    # put in command
                    db_engine_config['METADATA'].create_all(db_backend.engine)
                return db_backend
        return None

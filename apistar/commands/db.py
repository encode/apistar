from apistar.db import DBBackend


def create_tables():
    """
    Create SQLAlchemy tables.
    """
    from apistar.main import get_current_app
    app = get_current_app()
    db_backend = DBBackend.build(db_engine_config=app.db_engine_config)
    db_backend.create_tables()

import click

from apistar.db import DBBackend


def create_tables():
    """
    Create SQLAlchemy tables.
    """
    from apistar.main import get_current_app
    app = get_current_app()
    db_backend = DBBackend.build(db_config=app.settings.get('DATABASE', {}))
    db_backend.create_tables()
    click.echo("Tables created")

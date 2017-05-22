import click


def create_tables():
    """
    Create SQLAlchemy tables.
    """
    from apistar.cli import get_current_app
    from apistar.backends import SQLAlchemy
    app = get_current_app()
    db_backend = SQLAlchemy.build(settings=app.settings)
    db_backend.create_tables()
    click.echo("Tables created")

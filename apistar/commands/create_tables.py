import click


def create_sqlalchemy_tables():
    """
    Create SQLAlchemy tables.
    """
    from apistar.main import get_current_app
    from apistar.backends import SQLAlchemy
    app = get_current_app()
    db_backend = SQLAlchemy.build(settings=app.settings)
    db_backend.create_tables()
    click.echo("Tables created")

def create_django_tables():
    """
    Create DjangoBackend tables.
    """
    from apistar.main import get_current_app
    from apistar.backends import DjangoBackend
    app = get_current_app()
    db_backend = DjangoBackend.build(settings=app.settings)
    db_backend.create_tables()
    click.echo("Tables created")

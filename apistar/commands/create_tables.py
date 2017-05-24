import click
from apistar import schema


class Message(schema.String):
    pass


class Revision(schema.String):
    pass


def _get_sqlalchemy_backend():
    """
    Return the SQLAlchemyBackend.
    """
    from apistar.cli import get_current_app
    from apistar.backends.sqlalchemy_backend import SQLAlchemy
    app = get_current_app()
    return SQLAlchemy.build(settings=app.settings)


def _get_django_backend():
    """
    Return the DjangoBackend.
    """
    from apistar.cli import get_current_app
    from apistar.backends.django_backend import DjangoBackend
    app = get_current_app()
    return DjangoBackend.build(settings=app.settings)


def create_sqlalchemy_tables() -> None:
    """
    Create SQLAlchemy tables.
    """
    db_backend = _get_sqlalchemy_backend()
    db_backend.create_tables()
    click.echo("Tables created")


def django_makemigrations() -> None:
    """
    Makemigrations DjangoBackend.
    """
    db_backend = _get_django_backend()
    db_backend.makemigrations()
    click.echo("makemigrations")


def django_migrate() -> None:
    """
    Migrate DjangoBackend.
    """
    db_backend = _get_django_backend()
    db_backend.migrate()
    click.echo("migrate")


def django_showmigrations() -> None:
    """
    Show Migrations DjangoBackend.
    """
    db_backend = _get_django_backend()
    db_backend.showmigrations()
    click.echo("showmigrations")


def alembic_init() -> None:
    """
    Alembic Initialize SQLAlchemyBackend.
    """
    db_backend = _get_sqlalchemy_backend()
    db_backend.initialize()
    click.echo("Initialize alembic migrations")


def alembic_revision(message: Message) -> None:
    """
    Alembic Revision SQLAlchemyBackend.
    """
    db_backend = _get_sqlalchemy_backend()
    db_backend.revision(message=message)
    click.echo("revision: %s" % message)


def alembic_downgrade(revision: Revision) -> None:
    """
    Alembic Upgrade SQLAlchemyBackend.
    """
    db_backend = _get_sqlalchemy_backend()
    db_backend.downgrade(revision=revision)
    click.echo("Downgrade to revision: %s" % revision)


def alembic_upgrade(revision: Revision) -> None:
    """
    Alembic Upgrade SQLAlchemyBackend.
    """
    db_backend = _get_sqlalchemy_backend()
    db_backend.upgrade(revision=revision)
    click.echo("upgrade to revision: %s" % revision)

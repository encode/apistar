"""
Simple usage:

from apistar.frameworks.wsgi import WSGIApp as App
from apistar.backends.peewee_orm import PeeweeORM
from peewee import *

routes = [
   # ...
]

# Configure database settings.
settings = {
    'DATABASE': {
        'engine': 'PostgresqlDatabase',
        'database': '...',
        'host': 'localhost',
        'port': 5432,
        'user': '...',
        'password': '...'
    }
}

db = peewee_orm.PeeweeORM()

app = App(
    routes=routes,
    settings=settings,
    commands=db.commands,  # Install custom commands.
    components=db.components  # Install custom components.
)

class Customer(db.Model):
    name = CharField()


Interacting with the database:

from apistar.backends.peewee_orm import Session

def create_customer(session: Session, name: str):
    customer = session.Customer(name=name)
    customer.save()
    return {'id': customer.id, 'name': customer.name}

"""

import contextlib
import importlib
import typing
import peewee
from playhouse import pool
from peewee import Database
from apistar import Command, Component, Settings, exceptions
from apistar.interfaces import Console


class Session:

    def __init__(self, context):
        self._context = context

    @property
    def db(self):
        return self._context.database

    @property
    def transaction(self):
        return self._context.transaction


class PeeweeORM:

    def __init__(self, engine=None, defaults=None, config_key=None, imports=None,
                 migrate_dir='migrations', migrate_table='migratehistory'):
        self._initialized = False
        if engine is None:
            self.db = peewee.Proxy()
        else:
            self.db = engine(None)
        self.config_key = config_key
        self.defaults = defaults
        self.imports = imports
        self.migrate_dir = migrate_dir
        self.migrate_table = migrate_table
        self.models = []

        class Model(peewee.Model):
            def __init_subclass__(cls, **kwargs):
                super().__init_subclass__(**kwargs)
                if hasattr(self.Session, cls.__name__):
                    raise exceptions.ConfigurationError(
                        "Model with name %s is already registered"
                        )
                setattr(self.Session, cls.__name__, cls)
                self.models.append(cls)

            class Meta:
                database = self.db

        self.Model = Model
        self.Session = type('Session', (Session,), {})
        self.components = [
            Component(PeeweeORM, init=self.get_orm),
            Component(Database, init=get_database),
            Component(Session, init=get_session, preload=False)
        ]
        self.commands = [
            Command('create_tables', create_tables),
            Command('drop_tables', drop_tables),
            Command('make_migrations', make_migrations),
            Command('list_migrations', list_migrations),
            Command('migrate', migrate)
        ]

    def get_orm(self, settings: Settings):
        assert not self._initialized, "Peewee ORM is already initialized"
        if self.defaults is None:
            database_settings = {}
        else:
            database_settings = dict(self.defaults)

        config = settings['DATABASE']
        if self.config_key is not None:
            config = config[self.config_key]
        database_settings.update(config)

        self.imports = database_settings.pop('imports', self.imports)
        self.migrate_dir = database_settings.pop('migrate_dir', self.migrate_dir)
        self.migrate_table = database_settings.pop('migrate_table', self.migrate_table)

        if isinstance(self.db, peewee.Proxy):
            engine = database_settings.pop('engine', 'SqliteDatabase')
            engine_class = getattr(peewee, engine, None)
            if engine_class is None:
                engine_class = getattr(pool, engine, None)
            if not isinstance(engine_class, type) or not issubclass(engine_class, peewee.Database):
                raise exceptions.ConfigurationError('unknown peewee database engine')
            db = engine_class(**database_settings)
            self.db.initialize(db)
        else:
            self.db.init(**database_settings)
        self.import_modules()
        self._initialized = True
        return self

    def import_modules(self):
        if not self.imports:
            return
        for module in self.imports:
            try:
                importlib.import_module(module)
            except ImportError:
                pass


def get_database(orm: PeeweeORM) -> Database:
    return orm.db


@contextlib.contextmanager
def get_session(orm: PeeweeORM) -> typing.Generator[Session, None, None]:
    """
    Create a new context-managed database session, which automatically
    handles rollback or commit behavior.

    Args:
      orm: The configured database backend.
    """
    with orm.db.execution_context() as context:
        yield orm.Session(context)


def abstract():
    def wrapper(cls):
        cls._isabstract = True
    return wrapper


def get_non_abstract_models(orm):
    models = []
    for model in orm.models:
        # special case for abstract models
        if (model.__name__.startswith('_') or
                model.__name__.startswith('Abstract') or
                getattr(model, '_isabstract', False)):
            continue
        models.append(model)
    return models


def create_tables(orm: PeeweeORM):
    """Create non-abstract tables"""
    models = get_non_abstract_models(orm)
    orm.db.create_tables(models, safe=True)


def drop_tables(orm: PeeweeORM):
    """Drop all tables"""
    orm.db.drop_tables(orm.models, safe=True)


def get_router(orm):
    from peewee_migrate import Router
    return Router(orm.db, migrate_dir=orm.migrate_dir, migrate_table=orm.migrate_table)


def make_migrations(console: Console, orm: PeeweeORM, name: str=''):
    """Create migrations (peewee_migrate must be installed)"""
    from datetime import datetime
    if not name:
        name = datetime.now().strftime('migration_%Y%m%d%H%M')
    router = get_router(orm)
    models = get_non_abstract_models(orm)
    router.create(name=name, auto=models)


def list_migrations(console: Console, orm: PeeweeORM):
    """List migrations (peewee_migrate must be installed)"""
    router = get_router(orm)
    console.echo('Migrations are done:')
    console.echo('\n'.join(router.done))
    console.echo('')
    console.echo('Migrations are undone:')
    console.echo('\n'.join(router.diff))


def migrate(console: Console, orm: PeeweeORM, migration: str=''):
    """Run migrations (peewee_migrate must be installed)"""
    router = get_router(orm)
    if migration:
        run_migrations = []
        if migration == 'zero' or migration in router.done:
            downgrade = True
            for name in reversed(router.done):
                if name == migration:
                    break
                run_migrations.append(name)
        elif migration in router.diff:
            downgrade = False
            for name in router.diff:
                run_migrations.append(name)
                if name == migration:
                    break
        else:
            console.echo('Unknown migration %s' % migration)
    else:
        downgrade = False
        run_migrations = router.diff

    if not run_migrations:
        console.echo('There is nothing to migrate')

    else:
        for name in run_migrations:
            router.run_one(name, router.migrator, fake=False, downgrade=downgrade)

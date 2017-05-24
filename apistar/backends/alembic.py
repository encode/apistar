from alembic import command
from alembic.config import Config


class AlembicMigration(object):

    preload = True
    _loaded = False

    def upgrade(self, revision="head"):
        alembic_cfg = Config("alembic.ini")
        with self.engine.begin() as connection:
            alembic_cfg.attributes['connection'] = connection
            command.upgrade(alembic_cfg, revision=revision)

    def revision(self, message):
        alembic_cfg = Config("alembic.ini")
        with self.engine.begin() as connection:
            alembic_cfg.attributes['connection'] = connection
            command.revision(alembic_cfg, message=message)

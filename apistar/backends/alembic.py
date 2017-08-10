from typing import Callable
from alembic import command
from alembic.config import Config


class AlembicMigration(object):
    preload = True
    _loaded = False
    _migrations_directory = "migrations"

    def __init__(self):
        self.engine = None

    def _get_alembic_config(self, config_file="alembic.ini"):
        alembic_cfg = Config(config_file)
        alembic_cfg.set_main_option("script_location",
                                    self._migrations_directory)
        alembic_cfg.set_main_option("sqlalchemy.url", self.db_url)
        return alembic_cfg

    def _run_alembic_command(self, alembic_cmd: Callable, *args, **kwargs):
        alembic_cfg = self._get_alembic_config()
        with self.engine.begin() as connection:
            alembic_cfg.attributes['connection'] = connection
            alembic_cmd(alembic_cfg, *args, **kwargs)

    def initialize(self):
        self._run_alembic_command(command.init, directory=self._migrations_directory)

    def downgrade(self, revision):
        self._run_alembic_command(command.downgrade, revision=revision)

    def upgrade(self, revision):
        self._run_alembic_command(command.upgrade, revision=revision)

    def show(self, revision):
        self._run_alembic_command(command.show, rev=revision)

    def revision(self, message):
        self._run_alembic_command(command.revision, message=message)

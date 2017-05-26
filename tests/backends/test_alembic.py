from os import environ
from sqlalchemy.ext.declarative import declarative_base

import apistar
from apistar import App, test
from apistar.commands import (
    alembic_downgrade, alembic_init, alembic_revision, alembic_show,
    alembic_upgrade
)
from apistar.test import CommandLineRunner

Base = declarative_base()

app = App(
    routes=[],
    settings={
        "DATABASE": {
            "URL": environ.get('DB_URL', 'sqlite:///test.db'),
            "METADATA": Base.metadata,
        }
    },
    commands=[alembic_init, alembic_downgrade, alembic_revision, alembic_upgrade, alembic_show]
)

client = test.TestClient(app)
runner = CommandLineRunner(app)


def test_migrations(monkeypatch):
    def mock_get_current_app():
        return app

    monkeypatch.setattr(apistar.cli, 'get_current_app', mock_get_current_app)

    with runner.isolated_filesystem():
        result = runner.invoke(['alembic_init'])
        assert 'migrations' in result.output
        result = runner.invoke(['alembic_revision', 'test'])
        assert 'revision' in result.output
        result = runner.invoke(['alembic_upgrade', 'head'])
        assert 'upgrade' in result.output
        result = runner.invoke(['alembic_downgrade', 'head'])
        assert 'Downgrade' in result.output
        result = runner.invoke(['alembic_show'])
        assert 'migrations' in result.output

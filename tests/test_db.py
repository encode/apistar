import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

import apistar
from apistar import App, DBBackend, http, routing, test
from apistar.test import CommandLineRunner

Base = declarative_base()


class Kitten(Base):  # type: ignore
    __tablename__ = "Kitten"
    id = Column(Integer, primary_key=True)
    name = Column(String)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name
        }


def list_kittens(db_backend: DBBackend):
    session = db_backend.session_class()
    kittens = session.query(Kitten).all()
    return {
        'kittens': [kitten.serialize() for kitten in kittens]
    }


def create_kitten(db_backend: DBBackend, name: http.QueryParam):
    session = db_backend.session_class()
    add_kitten = Kitten(name=name)
    session.add(add_kitten)
    session.commit()
    return add_kitten.serialize()


app = App(
    routes=[
        routing.Route('/kittens/create/', 'GET', create_kitten),
        routing.Route('/kittens/', 'GET', list_kittens),
    ],
    settings={
        "DATABASE": {
            "TYPE": "SQLALCHEMY",
            "URL": 'sqlite:///test.db',
            "METADATA": Base.metadata
        }
    }
)


client = test.TestClient(app)
runner = CommandLineRunner(app)


@pytest.fixture
def clear_db(scope="function"):
    yield
    db_backend = DBBackend.build(db_config=app.settings['DATABASE'])
    db_backend.drop_tables()


def test_list_create(monkeypatch, clear_db):

    def mock_get_current_app():
        return app

    monkeypatch.setattr(apistar.main, 'get_current_app', mock_get_current_app)

    result = runner.invoke(['create_tables'])
    assert 'Tables created' in result.output

    response = client.get('http://example.com/kittens/create/?name=minky')
    assert response.status_code == 200
    created_kitten = response.json()
    assert created_kitten['name'] == 'minky'

    response = client.get('http://example.com/kittens/')
    assert response.status_code == 200
    assert response.json() == {'kittens': [created_kitten]}


def test_bad_db_component_config():
    bad_config = {
        "DATABASE": {
            "TYPE": "SQLALCHEMY",
        }
    }

    db_backend = DBBackend.build(db_config=bad_config)
    assert db_backend is None

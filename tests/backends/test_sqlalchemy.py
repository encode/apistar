import typing

import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from apistar import App, Route, TestClient, http, typesystem
from apistar.backends import sqlalchemy_backend
from apistar.backends.sqlalchemy_backend import Session

Base = declarative_base()


class KittenRecord(Base):  # type: ignore
    __tablename__ = "Kitten"
    id = Column(Integer, primary_key=True)
    name = Column(String)


class Kitten(typesystem.Object):
    properties = {
        'id': typesystem.Integer,
        'name': typesystem.String
    }


def list_kittens(session: Session) -> typing.List[Kitten]:
    records = session.query(KittenRecord).all()
    return [Kitten(record) for record in records]


def create_kitten(session: Session, name: http.QueryParam, force_fail: http.QueryParam) -> Kitten:
    record = KittenRecord(name=name)
    session.add(record)
    session.flush()
    if force_fail:
        raise Exception
    return Kitten(record)


routes = [
    Route('/kittens/', 'GET', list_kittens),
    Route('/kittens/', 'POST', create_kitten),
]

settings = {
    "DATABASE": {
        "URL": 'sqlite://',
        "METADATA": Base.metadata
    }
}

app = App(
    routes=routes,
    settings=settings,
    commands=sqlalchemy_backend.commands,
    components=sqlalchemy_backend.components
)


client = TestClient(app)


@pytest.fixture
def setup_tables(scope="function"):
    app.main(['create_tables'])
    yield
    app.main(['drop_tables'])


def test_list_create(setup_tables):
    # Successfully create a new record.
    response = client.post('/kittens/?name=minky')
    assert response.status_code == 200
    created_kitten = response.json()
    assert created_kitten['name'] == 'minky'

    # List all the existing records.
    response = client.get('/kittens/')
    assert response.status_code == 200
    assert response.json() == [created_kitten]

    # Rollback a session without creating a new record.
    with pytest.raises(Exception):
        response = client.post('/kittens/?name=fluffums&force_fail=1')
    response = client.get('/kittens/')
    assert response.status_code == 200
    assert response.json() == [created_kitten]

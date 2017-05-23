from os import environ

import dj_database_url

import apistar
from apistar import App, http, routing, test
from apistar.backends import DjangoBackend
from apistar.commands import django_makemigrations, django_migrate
from apistar.test import CommandLineRunner


def list_stars(orm: DjangoBackend):
    Star = orm.Star
    return {
        'stars': Star.objects.values('name', 'id')
    }


def create_star(orm: DjangoBackend, name: http.QueryParam):
    star = orm.Star(name=name)
    star.save()
    return {
        'star': {'name': star.name, 'id': star.id}
    }


app = App(
    routes=[
        routing.Route('/api/stars', 'GET', list_stars),
        routing.Route('/api/stars/create', 'GET', create_star),
    ],
    settings={
        'DATABASES': {
            'default': dj_database_url.config(
                default=environ.get('DB_URL', 'sqlite:///test.db')
            )
        },
        'INSTALLED_APPS': ['django_project']
    },
    commands=[django_makemigrations, django_migrate]
)


client = test.TestClient(app)
runner = CommandLineRunner(app)


def test_list_create(monkeypatch):

    def mock_get_current_app():
        return app

    monkeypatch.setattr(apistar.main, 'get_current_app', mock_get_current_app)

    result = runner.invoke(['django_makemigrations'])
    assert 'makemigrations' in result.output
    result = runner.invoke(['django_migrate'])
    assert 'migrate' in result.output

    response = client.get('http://example.com/api/stars/create?name=mars')
    assert response.status_code == 200
    created_star = response.json()
    assert created_star['star']['name'] == 'mars'

    response = client.get('http://example.com/api/stars')
    assert response.status_code == 200
    assert response.json() == {'stars': [created_star['star']]}

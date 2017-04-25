from apistar import environment, schema


class Env(environment.Environment):
    properties = {
        'DEBUG': schema.Boolean,
        'DATABASE_URL': schema.String
    }


def test_env():
    env = Env({
        'DEBUG': 'False',
        'DATABASE_URL': 'sqlite:///test.db'
    })
    assert env['DEBUG'] is False
    assert env['DATABASE_URL'] == 'sqlite:///test.db'

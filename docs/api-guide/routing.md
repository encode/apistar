# Routing

Use `{curly_braces}` in your URL conf to include a URL path parameter.

```python
from apistar import App, Route


def echo_username(username: str) -> dict:
    return {'message': 'Welcome, %s!' % username}


routes = [
    Route('/users/{username}/', method='GET', handler=echo_username)
]

app = App(routes=routes)
```

Use type annotation on a handler to match integers or floats in the URL string.

```python
from apistar import App, Route, exceptions


USERS = {1: 'hazel', 2: 'james', 3: 'ana'}

def echo_username(user_id: int) -> dict:
    if user_id not in USERS:
        raise exceptions.NotFound()
    return {'message': 'Welcome, %s!' % USERS[user_id]}

routes = [
    Route('/users/{user_id}/', method='GET', handler=echo_username)
]

app = App(routes=routes)
```

If you want to capture a complete URL path parameter *including any `/`
characters* then use `{+curly_braces}`.

```python
routes = [
    Route('/static/{+path}', method='GET', handler=serve_file)
]

app = App(routes=routes)
```

### Building URLS

You can generate URL strings that match your routing configuration by using `app.reverse_url(name, **parameters)`.

```python
from apistar import App, Route, exceptions


USERS = {1: 'hazel', 2: 'james', 3: 'ana'}

def list_users(app: App) -> list:
    return [
        {
            'username': username,
            'url': app.reverse_url('get_user', user_id=user_id)
        } for user_id, username in USERS.items()
    ]

def get_user(app: App, user_id: int) -> dict:
    if user_id not in USERS:
        raise exceptions.NotFound()
    return {
        'username': USERS[user_id],
        'url': app.reverse_url('get_user', user_id=user_id)
    }

routes = [
    Route('/users/', method='GET', handler=list_users),
    Route('/users/{user_id}/', method='GET', handler=get_user)
]

app = App(routes=routes)
```

### Routing in larger projects

In many projects you may want to split your routing into different sections.
Use `Include` to add a list of routes under a single URL prefix.

**myproject/users.py**

```python
from apistar import App, Route, exceptions


USERS = {1: 'hazel', 2: 'james', 3: 'ana'}

def list_users(app: App) -> list:
    return [
        {
            'username': username,
            'url': app.reverse_url('users:get_user', user_id=user_id)
        } for user_id, username in USERS.items()
    ]

def get_user(app: App, user_id: int) -> dict:
    if user_id not in USERS:
        raise exceptions.NotFound()
    return {
        'username': USERS[user_id],
        'url': app.reverse_url('users:get_user', user_id=user_id)
    }

routes = [
    Route('/', method='GET', handler=list_users),
    Route('/{user_id}', method='GET', handler=get_user),
]
```

**app.py:**

```python
from apistar import App, Include
from myproject import users

routes = [
    Include('/users', name='users', routes=users.routes),
    ...
]

app = App(routes=routes)
```

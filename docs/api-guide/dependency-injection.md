# Dependency Injection

API Star allows you to include various parameters on handler functions and
event hooks, and will automatically provide those parameters as required.

You can add additional components, making them available to handler functions
if they are included in an annotation.

Here's an example that makes the `User` annotation available to handler functions.

```python
from apistar import App, Route, exceptions, http
from apistar.server.components import Component


class User(object):
    def __init__(self, username: str):
        self.username = username


class UserComponent(Component):
    def resolve(authorization: http.Header) -> User:
        """
        Determine the user associated with a request, using HTTP Basic Authentication.
        """
        if authorization is None:
            return None

        scheme, token = authorization.split()
        if scheme.lower() != 'basic':
            return None

        username, password = base64.b64decode(token).decode('utf-8').split(':')
        if not self.check_authentication(username, password):
            raise exceptions.PermissionDenied('Incorrect username or password.')

        return User(username)

    def check_authentication(self, username: str, password: str) -> bool:
        # Just an example here. You'd normally want to make a database lookup,
        # and check against a hash of the password.
        return password == 'secret'


def hello_user(user: User=None) -> dict:
    return {'hello': user.username if user else None}


routes = [
    Route('/', method='GET', handler=hello_user)
]
components = [UserComponent()]

app = App(routes=routes, components=components)
```

You can combine components and event hooks in order to have a component
that always runs, regardless of if it is used in a handler function.

```python
class MustBeAuthenticated():
    def on_request(self, user: User=None) -> None:
        if user is None:
            raise exceptions.NotAuthenticated()


def hello_user(user: User) -> dict:
    return {'hello': user.username}


routes = [
    Route('/', method='GET', handler=hello_user)
]
components = [UserComponent()]
event_hooks = [MustBeAuthenticated()]

app = App(routes=routes, components=components, event_hooks=event_hooks)
```

## Reference

The following components are already installed by default.

Class                          | Notes
-------------------------------|-------
http.Method                    |
http.URL                       |
http.Scheme                    |
http.Host                      |
http.Port                      |
http.Path                      |
http.QueryString               |
http.QueryParams               |
http.QueryParam                | A single query parameter, looked up against the parameter name.
http.Headers                   |
http.Header                    | A single query parameter, looked up against the parameter name.
http.Body                      |
http.Request                   |
http.PathParams                | The matched path parameters for the incoming request.
App                            | The current application. Made available as `App` for both sync and async applications.
Route                          | The matched route for the incoming request.
Exception                      | `None` unless exception handling is running.
server.wsgi.WSGIEnviron        | Only for `App`.
server.wsgi.WSGIStartResponse  | Only for `App`.
server.asgi.ASGIScope          | Only for `ASyncApp`.
server.asgi.ASGIReceive        | Only for `ASyncApp`.
server.asgi.ASGISend           | Only for `ASyncApp`.

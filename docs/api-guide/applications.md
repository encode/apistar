# Applications

The first thing you'll always need to do when creating a new API Star service
is to create an application instance.

Here's an example that just returns a simple HTML homepage:

```python
from apistar import App, Route


def homepage() -> str:
    return '<html><body><h1>Homepage</h1></body></html>'


routes = [
    Route('/', method='GET', handler=homepage),
]

app = App(routes=routes)
```

## Sync or ASync

API Star supports both multi-threaded (WSGI) and asyncio (ASGI) modes of operation.

The Python ecosystem currently has far more support for multi-threaded concurrency.
Most existing database adapters, ORMs, and other networking components are
designed to work within this context. If you're not sure which of the two modes
you want, then you probably want to use the standard `App` instance.

For IO-bound web services where you need particularly high throughput
you might want to choose the asyncio mode. If you do so then you'll need to
make sure that you're only ever making network requests or disk access using
async operations, and packages designed to work with asyncio.

For an asyncio-based application, you should use the `ASyncApp` class.

Once you're using `ASyncApp` you'll be able to route to either standard
functions, or to `async` functions.

```python
from apistar import ASyncApp, Route

async def hello_world() -> dict:
    # We can perform some network I/O here, asyncronously.
    return {'hello': 'async'}

routes = [
    Route('/', method='GET', handler=hello_world)
]

app = ASyncApp(routes=routes)
```

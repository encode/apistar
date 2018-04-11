# Event Hooks

Sometimes you'll want to always run some code before or after a handler function.

API Star provides something very similar to middleware, that lets you register
a group of functions to be run in response to particular events.

Here's an example...

```python
class CustomHeadersHook():
    def on_response(self, response: http.Response):
        response.headers['x-custom'] = 'Ran on_response()'
        return response

event_hooks = [CustomHeadersHook()]

app = App(routes=routes, event_hooks=event_hooks)
```

An event hook instance may include any or all of the following methods:

* `on_request(self)` - Runs before the handler function.
* `on_response(self, response, ...)` - Runs after the handler function. Should return the response.
* `on_error(self, response, ...)` - Runs after any exception occurs. Should return the response.

The signature of the method may include any components that would be available
on a handler function.

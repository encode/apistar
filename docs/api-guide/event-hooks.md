# Event Hooks

Sometimes you'll want to always run some code before or after a handler function.

API Star provides something very similar to middleware, that lets you register
a group of functions to be run in response to particular events.

Here's an example...

```python
class CustomHeadersHook():
    def on_response(self, response: http.Response):
        response.headers['x-custom'] = 'Ran on_response()'

event_hooks = [CustomHeadersHook()]

app = App(routes=routes, event_hooks=event_hooks)
```

An event hook instance may include any or all of the following methods:

* `on_request(self, ...)` - Runs before the handler function.
* `on_response(self, ...)` - Runs after the handler function, or when a handled exception occurs.
* `on_error(self, ...)` - Runs after any unhandled exception occurs.

The signature of the method may include any annotations that would be available
on a handler function, or the `http.Response` annotation.

## Error handling

Subclasses of `HTTPException` are dealt with by the applications exception handler,
and return responses, that pass through any `on_response` hooks as usual.

Unhandled exceptions result in server errors, and should be treated differently.
For these cases, any installed `on_error` event hooks will be run. This event hook
allows you to monitor or log exceptions.

It's recommend that use of `on_error` event hooks should be kept to a minimum,
dealing only with whatever error monitoring is required. Any exceptions thrown
in one of these handlers will result in the raw exception being raised to the
webserver with no further error handling taking place.

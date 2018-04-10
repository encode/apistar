# Requests and Responses

## Requests

To access the incoming HTTP request, use the `http.Request` class as an
annotation on the handler function.

```python
from apistar import http


def echo_request_info(request: http.Request) -> dict:
    return {
        'method': request.method,
        'url': request.url,
        'headers': dict(request.headers),
        'body': request.body.decode('utf-8')
    }
```

API Star allows you to dynamically inject various other information about the
incoming request into your views using type annotation.

```python
from apistar import http


def echo_query_params(query_params: http.QueryParams) -> dict:
    return {
        'params': dict(query_params)
    }

def echo_user_agent(user_agent: http.Header) -> dict:
    return {
        'user-agent': user_agent
    }
```

Some of the components you might use most often:

| Component          | Description |
| ------------------ | ----------- |
| `http.Request`     | The HTTP request. Includes `.method`, `.url`, and `.headers` attributes. |
| `http.Headers`     | The request headers, returned as a dictionary-like object. |
| `http.Header`      | Lookup a single request header, corresponding to the argument name.<br/>Returns a string or `None`. |
| `http.QueryParams` | The request query parameters, returned as a dictionary-like object. |
| `http.QueryParam`  | Lookup a single query parameter, corresponding to the argument name.<br/>Returns a string or `None`. |
| `http.Body`        | The request body, as a bytestring. |

## Responses

By default API star uses HTML responses for handlers that return strings,
and JSON responses for anything else.

```python
def hello_world() -> dict:
    return {'text': 'Hello, world!'}
```

For more control over the response use the `JSONResponse` and
`HTMLResponse` classes.

```python
from apistar import http


def hello_world(accept_language: http.Header) -> http.JSONResponse:
    if 'de' in accept_language:
        data = {'text': 'Hallo, Welt!'}
    else:
        data = {'text': 'Hello, world!'}
    headers = {'Vary': 'Accept-Language'}
    return http.JSONResponse(data, status_code=200, headers=headers)
```

For other content types, use a `Response` class, and set the content-type
header explicitly.

```python
from apistar import http


def hello_world() -> http.Response:
    content = 'Hello, world!'
    headers = {'Content-Type': 'text/plain'}
    return http.Response(content, headers=headers)
```

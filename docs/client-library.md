# Client Library

API Star includes a dynamic client library.

Typically developers have had to build client libraries for each new
API service, or auto-generate a new client on each new release.

The API Star dynamic client library works differently, in that it simply
takes the API schema as an argument when the client is instantiated,
and then allows you to interact with the API.

```python
schema = {
    ...
}

client = apistar.Client(schema)
result = client.request('listWidgets', search='cogwheel')
```

## Instantiating a client

## Making requests

## Authentication

## Decoding responses

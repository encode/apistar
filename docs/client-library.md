# Client Library

API Star includes a dynamic client library.

Typically developers have had to build client libraries for each new
API service, or auto-generate a new client on each new release.

The API Star dynamic client library works differently, in that it simply
takes the API schema as an argument when the client is instantiated,
and then allows you to interact with the API.

```python
import apistar


schema = """
openapi: 3.0.0
info:
  title: Widget API
  version: '1.0'
  description: An example API for widgets
paths:
  /widgets:
    get:
      summary: List all the widgets.
      operationId: listWidgets
      parameters:
      - in: query
        name: search
        description: Filter widgets by this search term.
        schema:
          type: string
"""

client = apistar.Client(schema)
result = client.request('listWidgets', search='cogwheel')
```

## Instantiating a client

You can instantiate an API client like so:

```python
import apistar

client = apistar.Client(schema=...)
```

Signature: `Client(schema, format=None, encoding=None, auth=None, decoders=None, encoders=None, headers=None, session=None, allow_cookies=True)`

* `schema` - An OpenAPI or Swagger schema. This can be passed either as a dict instance,
or as a JSON or YAML encoded string/bytestring.
* `format` - Either "openapi" or "swagger". You can leave this as None to have the
schema format be automatically inferred.
* `encoding` - If passing the schema as a string/bytestring, this argument may
be used to specify either `"json"` or `"yaml"`.  If not included, the encoding will
be inferred from the content if possible.
* `auth` - Any authentication class to set on the request session.
* `decoders` - Any decoders to enable for decoding the response content.
* `encoders` - Any encoders to enable for encoding the request content.
* `headers` - A dictionary of custom headers to use on every request.
* `session` - A requests `Session` instance to use for making the outgoing HTTP requests.
* `allow_cookies` - May be set to `False` to disable `requests` standard cookie handling.

## Making requests

Requests to the API are made using the `request` method, including the operation id
and any parameters.

```python
result = client.request('listWidgets', search='cogwheel')
```

## Authentication

You can use any standard `requests` authentication class with the API client.

```python
import apistar
from requests.auth import HTTPDigestAuth

schema = {...}

auth = HTTPDigestAuth('user', 'pass')
client = apistar.Client(schema=schema, auth=auth)
```

API Star also includes some authentication classes that you can use for making
API requests.

* `apistar.client.auth.TokenAuthentication(token, scheme="Bearer")` - Allows token
authenticated HTTP requests, including an `Authorization: Bearer <token>` header in
all outgoing requests.
* `apistar.client.auth.SessionAuthentication(csrf_cookie_name, csrf_header_name)` - Allows
session authenticated requests that are CSRF protected. The API will need to expose a login
operation.

## Decoding responses

The return result is determined from the response by selecting a decoder based
on the response content-type header, and allowing it to decode the response content.

By default the client has the following decoders enabled:

* `apistar.client.decoders.JSONDecoder` - Handles `application/json` responses. The return result will be the decoded data structure.
* `apistar.client.decoders.TextDecoder` - Matches `text/*`, and handles any text responses. The return result will be a string.
* `apistar.client.decoders.DownloadDecoder` - Matches `*/*`, and handles any other responses. The return result will be a temporary file, which will be deleted once closed or no longer referenced.

You can customize which decoders are installed on a client like so:

```python
client = apistar.Client(schema, decoders=[JSONDecoder()])
```

In the example above the client would send `application/json` in the `Accept` header,
and would raise an error on any other content being returned.

### Writing a custom decoder

To write a custom decoder you should subclass `apistar.client.decoders.BaseDecoder`,
and override the `media_type` attribute, and the `decode(self, response)` method.

For example:

```python
from apistar.client.decoders import BaseDecoder
import csv


class CSVDecoder(BaseDecoder):
    media_type = 'text/csv'

    def decode(self, response):
        lines = response.text.splitlines()
        reader = csv.reader(lines, delimiter=',')
        return [row for row in reader]
```

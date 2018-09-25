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

The `result` will be a data structure, decoded appropriately from the response
content, as determined by the `Content-Type` header of the response.

In the event of an error response (4xx or 5xx status codes) the client will
raise `apistar.exceptions.ErrorResponse`.

There are three attributes on here that you may wish to inspect:

* `.title` - A string indicating the response status code/phrase. Eg. `"400 Bad Request"`
* `.status_code` - An integer indicating the response status code. Eg. `400`
* `.content - The decoded response content. Eg. `{"search": "Must be no more than 100 characters."}`

If the request is made with an incorrect set of parameters, or if the client
cannot fulfil the request for some reason then `apistar.exceptions.ClientError`
will be raised.

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

## Encoding requests

The request body is determined depending on the encoding used for the request.

By default the client has the following encoders enabled:

* `apistar.client.encoders.JSONEncoder` - Handles `application/json` requests.
* `apistar.client.encoders.MultiPartEncoder` - Handles `multipart/form-data` requests.
* `apistar.client.encoders.URLEncodedEncoder` - Handles `application/x-www-form-urlencoded` requests.

You can customize which decoders are installed on a client like so:

```python
client = apistar.Client(schema, encoders=[JSONEncoder()])
```

In the example above the client would send `application/json` in outgoing requests,
and would raise an error for requests which required any other encoding to be used.

### Writing a custom encoder

Typically the default set of encoders will be appropriate for handling the
encoding of the request body, since JSON or either of the types of form data
are by far the most commonly used encodings for HTTP requests. However you can
customize this behaviour if needed, in order to support endpoints which expect
some other type of encoding.

To write a custom encoded you should subclass `apistar.client.encoders.BaseEncoder`,
and override the `media_type` attribute, and the `encode(self, options, content)` method.

The `encode` method is used to modify the options that are passed to `requests.send(...)`
when making the outgoing request.

For example:

```python
from apistar.client.encoders import BaseEncoder


class TextEncoder(BaseDecoder):
    media_type = 'text/plain'

    def encode(self, options, content):
        assert isinstance(content, str), 'The request body for this endpoint must be a string.'
        options['headers']['content-type'] = 'text/plain'
        options['data'] = content
```

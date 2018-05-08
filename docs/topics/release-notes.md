# Release Notes

## Version 0.5.x

### 0.5.12

* The WSGI `exc_info` argument is a positional argument, not a keyword argument.

### 0.5.11

* Add API documentation support.

### 0.5.10

* Handle multiple keys in multipart content.

### 0.5.9

* `allow_null=True` sets default to `None` unless otherwise specified.

### 0.5.8

* Add support for response schemas to OpenAPI output.

### 0.5.7

* All `Type` annotations for GET handlers.

### 0.5.6

* Fix bool annotations.

### 0.5.5

* Fix nested types.

### 0.5.4

* Event hooks instantiated on each request/response cycle.

### 0.5.3

* Support multipart and urlencoded content in `RequestData`.
* Reverse ordering of `on_response` and `on_error` event hooks.

### 0.5.2

* Graceful handling of cases where `on_error` handling raises errors.

### 0.5.1

* Fix for handlers than annotate `Response`, not being available to the `ReturnValue` annotation when `render_response` is called.

### 0.5

* Should have introduced a proper version bump, given the 0.4.5 changes.

## Version 0.4.x

### 0.4.5

* on_response now runs for both regular reponses and handled exceptions.
* on_error now only runs for unhandled exceptions (ie. 500 reponses).
* Return 500 responses on error.
* Test client raises exceptions instead of returning 500 responses.
* Add debug flag to app.serve(), to switch between debugger vs. plain responses.
* Include `http.QueryParam` annotations in schema output, as one of the parameters.
* Include handler docstring in schema output, as the 'description'.
* Allow subclassing of `type.Type`.

### 0.4.4

* OpenAPI schema uses `requestBody` instead of the incorrect `responseBody`.
* Include `http.Response` component.
* Drop requirement of returning response from event hooks.
* Use `shutil.move` in preference to `os.rename` in `DownloadCodec`.

### 0.4.3

* Drop erroneous commit.

### 0.4.2

* Move `RESPONSE_STATUS_TEXT` out of `http` and into `wsgi`.

### 0.4.1

* Update package info.

### 0.4

The Version 0.4 release is a significant re-working of the API Star codebase.
As part of this there are a number of features that have been removed and not
yet made their way back in to the project:

* The API Docs have not yet been re-introduced.
* The command routing has not yet been re-introduced.
* The `apistar` command line tool has not yet been re-introduced.
* The ORM components have been removed. We'll be pushing for this kind of functionality to be addressed as third-party packages instead.

However the overall state of the project is in a much better place than it
was in 0.3, and I'm confident that we've now got a great base to build on.

We've also gained a number of new features and improvements:

* ASGI compatible. You'll be able to use either `uvicorn` or `daphne` as servers for use with ASyncApp.
* OpenAPI is now the default schema representation.
* We now have an event hooks API.
* The dependency injection now has a much cleaner, simpler API and implementation.
* The type system now has a much cleaner, simpler API and implementation.
* Settings are much cleaner, with each component configured at the point of instantiation, rather than one big global settings object that's available everywhere.

If you do need to continue working against the 0.3 version, you should refer
to [the older documentation on GitHub][0.3]. You should also make sure to serve any
async applications using uvicorn <= 0.0.15, which uses the pre-ASGI interface style.

[0.3]: https://github.com/encode/apistar/tree/0.3.9

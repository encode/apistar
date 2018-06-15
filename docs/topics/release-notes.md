# Release Notes

## Version 0.5.x

### 0.5.38

* Redesign API for retriving OpenAPI and Swagger validation errors.

### 0.5.37

* Swagger: Fixes to security and securityDefinitions.

### 0.5.36

* Resolve issue with `filename` argument on errors.

### 0.5.35

* Support optional `filename` argument against errors.

### 0.5.34

* OpenAPI: Add 'RequestBodies' to components.
* OpenAPI: 'security' must be a list.

### 0.5.33

* More robust handling for `None` in tags or titles in swagger/openapi codecs.

### 0.5.32

* Add 'swaggerui' option to `docs/theme`, alongside existing 'redoc', 'apistar'.

### 0.5.31

* Add 'docs/theme' section to `.apistar.yml` config file validation.

### 0.5.30

* Drop erronous `print`

### 0.5.29

* Initial support for validating `.apistar.yml` config file.

### 0.5.28

* First pass at Swagger 2 support (alongside existing OpenAPI 3 support).

### 0.5.27

* Handle error formatting for missing keys.

### 0.5.26

* Fix error reporting when YAML parse errors occur.

### 0.5.25

* More robust YAML errors.

### 0.5.24

* Fix issues with Docs API theme.

### 0.5.23

* Catch and handle `yaml.parser.ParserError` when parsing OpenAPI.

### 0.5.22

* Fix error when using `list` or `dict` as response annotations.
* Fix for error handling in ASyncApp.
* When attribute does not exist, raise AttributeError on `Type` instead of `KeyError`.
* Fix "not JSON serializable" error condition.

### 0.5.21

* Fix API docs in ASyncApp when `static_dir` is not defined.

### 0.5.20

* Fix static file links when rendering docs in ASyncApp

### 0.5.19

* API Documentation theme

### 0.5.18

* Fix parsing of OpenAPI documents with request bodies.

### 0.5.17

* Add 'SecurityScheme' to OpenAPI and allow 'responses' to use reference objects.

### 0.5.16

* Improved error formatting.

### 0.5.15

* Fix 'responses' and 'parameters' in OpenAPI spec.

### 0.5.14

* Added 'headers' to OpenAPI spec.

### 0.5.13

* Added `apistar docs <schema>` and `apistar validate <schema>`.

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

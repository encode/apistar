<div style="float: right">
    <a href="https://travis-ci.org/encode/apistar"><img style="border: none; background-color: transparent; margin: 0" alt="Build Status" src="https://travis-ci.org/encode/apistar.svg?branch=master"></a>
    <a href="https://codecov.io/gh/encode/apistar"><img style="border: none; background-color: transparent; margin: 0" alt="codecov" src="https://codecov.io/gh/encode/apistar/branch/master/graph/badge.svg"></a>
    <a href="https://pypi.python.org/pypi/apistar"><img style="border: none; background-color: transparent; margin: 0" alt="Package version" src="https://badge.fury.io/py/apistar.svg"></a>
</div>

# API Star

*The Web API toolkit.* 🛠

**Community:** [https://discuss.apistar.org/](https://discuss.apistar.org/) 🤔 💭 🤓 💬 😎

**Repository**: [https://github.com/encode/apistar](https://github.com/encode/apistar) 💻

---

API Star is a toolkit for working with OpenAPI or Swagger schemas. It allows you to:

* Build API documentation, with a selection of available themes.
* Validate API schema documents, and provide contextual errors.
* Validate requests and responses, using the API Star type system.
* Make API requests using the dynamic client library.

You can use it to build static documentation, integrate it within a Web framework,
or use it as the client library for interacting with other APIs.

## Quickstart

Install API Star:

```bash
$ pip3 install apistar
```

Let's take a look at some of the functionality the toolkit provides...

We'll start by creating an OpenAPI schema, `schema.yml`:

```yaml
openapi: 3.0.0
info:
  title: Widget API
  version: '1.0'
  description: An example API for widgets
servers:
  - url: https://www.example.org/
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
```

Let's also create a configuration file `apistar.yml`:

```yaml
schema:
  path: schema.yaml
  format: openapi
```

We're now ready to start using the `apistar` command line tool.

We can validate our OpenAPI schema:

```
$ apistar validate
✓ Valid OpenAPI schema.
```

Or build developer documentation for our API:

```
$ apistar docs --serve
✓ Documentation available at "http://127.0.0.1:8000/" (Ctrl+C to quit)
```

We can also make API requests to the server referenced in the schema:

```
$ apistar request listWidgets search=cogwheel
```

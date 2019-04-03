<p align="center">
    <img src="https://raw.githubusercontent.com/encode/apistar/master/docs/img/logo-200-square-light.png" alt="API Star" />
</p>
<p align="center">
    🛠 <em>The Web API toolkit.</em> 🛠
</p>
<p align="center">
<a href="https://travis-ci.org/encode/apistar">
    <img src="https://travis-ci.org/encode/apistar.svg?branch=master" alt="Build Status">
</a>
<a href="https://codecov.io/gh/encode/apistar">
    <img src="https://codecov.io/gh/encode/apistar/branch/master/graph/badge.svg" alt="codecov">
</a>
<a href="https://pypi.python.org/pypi/apistar">
    <img src="https://badge.fury.io/py/apistar.svg" alt="Package version">
</a>
</p>

---

**Community:** https://discuss.apistar.org 🤔 💭 🤓 💬 😎

**Documentation:** https://docs.apistar.com 📘

**Requirements:** Python 3.6+

---

API Star is a toolkit for working with OpenAPI or Swagger schemas. It allows you to:

* Build API documentation, with a selection of available themes.
* Validate API schema documents, and provide contextual errors.
* Make API requests using the dynamic client library.

You can use it to build static documentation, integrate it within a Web framework,
or use it as the client library for interacting with other APIs.

## Quickstart

Install API Star:

```bash
$ pip3 install apistar
```

Let's take a look at some of the functionality the toolkit provides...

We'll start by creating an OpenAPI schema, `schema.yaml`:

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

## Where did the server go?

With version 0.6 onwards the API Star project is being focused as a
framework-agnositic suite of API tooling. The plan is to build out this
functionality in a way that makes it appropriate for use either as a stand-alone
tool, or together with a large range of frameworks.

The 0.5 branch remains available on GitHub, and can be installed from PyPI
with `pip install apistar==0.5.41`. Any further development of the API Star
server would likely need to be against a fork of that, under a new maintainer.

If you're looking for a high-performance Python-based async framework, then
I would instead recommend [Starlette](https://www.starlette.io/).

---

<p align="center"><i>API Star is <a href="https://github.com/tomchristie/apistar/blob/master/LICENSE.md">BSD licensed</a> code.<br/>Designed & built in Brighton, England.</i>
<p align="center">
    <img src="https://raw.githubusercontent.com/encode/apistar/master/docs/img/ident-44-square-light.png" alt="API Star" />
</p>

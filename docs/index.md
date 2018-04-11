<div style="float: right">
    <a href="https://travis-ci.org/encode/apistar"><img style="border: none; background-color: transparent; margin: 0" alt="Build Status" src="https://travis-ci.org/encode/apistar.svg?branch=master"></a>
    <a href="https://codecov.io/gh/encode/apistar"><img style="border: none; background-color: transparent; margin: 0" alt="codecov" src="https://codecov.io/gh/encode/apistar/branch/master/graph/badge.svg"></a>
    <a href="https://pypi.python.org/pypi/apistar"><img style="border: none; background-color: transparent; margin: 0" alt="Package version" src="https://badge.fury.io/py/apistar.svg"></a>
</div>

# API Star

A smart Web API framework, designed for Python 3.

<!-- [![Build Status](https://travis-ci.org/encode/apistar.svg?branch=master)](https://travis-ci.org/encode/apistar)
[![codecov](https://codecov.io/gh/encode/apistar/branch/master/graph/badge.svg)](https://codecov.io/gh/encode/apistar)
[![Package version](https://badge.fury.io/py/apistar.svg)](https://pypi.python.org/pypi/apistar) -->

**Community:** [https://discuss.apistar.org/](https://discuss.apistar.org/) 🤔 💭 🤓 💬 😎

**Repository**: [https://github.com/encode/apistar](https://github.com/encode/apistar) 💻

---

## Quickstart

Install API Star:

```bash
$ pip3 install apistar
```

Create a new project in `app.py`:

```python
from apistar import App, Route


def welcome(name=None):
    if name is None:
        return {'message': 'Welcome to API Star!'}
    return {'message': 'Welcome to API Star, %s!' % name}


routes = [
    Route('/', method='GET', handler=welcome),
]

app = App(routes=routes)


if __name__ == '__main__':
    app.serve('127.0.0.1', 5000, use_debugger=True, use_reloader=True)
```

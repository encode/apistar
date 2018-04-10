# Templates

API Star is particularly designed around building APIs, but is equally
capable of being used to build web applications.

## Configuration

You'll need to install `jinja2` to use the default template backend.

To include templates in your application, create a directory to contain the templates,
and include it with the `template_dir` argument when instantiating the app.

```python
import os

BASE_DIR = os.path.dirname(__file__)
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

...

app = App(routes=routes, template_dir=TEMPLATE_DIR)
```

## Rendering templates

To render a template, use `app.render_template(template_name, **context)`.

**templates/index.html**:

```html
<html>
    <body>
        {% if name %}
        <h1>Hello, {{ name }}!</h1>
        {% else %}
        <h1>Hello!</h1>
        {% endif %}
    </body>
</html>
```

**app.py**:

```python
import os
from apistar import App, Route


BASE_DIR = os.path.dirname(__file__)
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')


def welcome(app: App, name=None):
    return app.render_template('index.html', name=name)

routes = [
    Route('/', method='GET', handler=welcome),
]

app = App(routes=routes, template_dir=TEMPLATE_DIR)


if __name__ == '__main__':
    app.serve('127.0.0.1', 8080, use_debugger=True)
```

You can configure where templates are served from by using the `template_dir`
argument when instantiating an application.

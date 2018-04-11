# Static Files

You'll need to install `whitenoise` to use the default static files backend.
If you're using `ASyncApp` you'll also need to install `aiofiles`.

To include static files in your application, create a directory to contain the static files,
and include it with the `static_dir` argument when instantiating the app.

```python
import os

BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, 'static')

...

app = App(routes=routes, static_dir=STATIC_DIR)
```

The default behavior is to serve static files from the URL prefix `/static/`.
You can modify this by also including a `static_url` argument.

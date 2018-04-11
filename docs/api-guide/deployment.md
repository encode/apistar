# Deployment

## The Development Server

You'll want to make sure to include `app.serve()` in your main `app.py` module:

```python
if __name__ == '__main__':
    app.serve('127.0.0.1', 5000, use_debugger=True, use_reloader=True)
```

For development you can now just run the application directly.

```bash
$ python app.py
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

## Running in Production

Which webserver you use depends on if you're running `App` or `ASyncApp`.

For `App` you can use any WSGI based webserver. Both `gunicorn` and `uwsgi`
are good options.

For `ASyncApp` you'll want to use an ASGI based webserver. Your options
here are `uvicorn` or `daphne`.

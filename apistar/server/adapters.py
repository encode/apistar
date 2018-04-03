import asyncio

from apistar.http import RESPONSE_STATUS_TEXT


class ASGItoWSGIAdapter(object):
    """
    Expose an WSGI interface, given an ASGI application.

    We want this so that we can use the werkzeug development server and
    debugger together with an ASGI application.
    """
    def __init__(self, asgi):
        self.asgi = asgi

    def __call__(self, environ, start_response):
        return_bytes = []
        message = self.environ_to_message(environ)
        asgi_coroutine = self.asgi(message)

        async def send(message):
            if message['type'] == 'http.response.start':
                status = RESPONSE_STATUS_TEXT[message['status']]
                headers = [
                    [key.decode('latin-1'), value.decode('latin-1')]
                    for key, value in message['headers']
                ]
                exc_info = None
                start_response(status, headers, exc_info)
            elif message['type'] == 'http.response.body':
                return_bytes.append(message.get('body', b''))

        async def recieve():
            return {
                'type': 'http.request',
                'body': environ['wsgi.input'].read()
            }

        loop = asyncio.get_event_loop()
        loop.run_until_complete(asgi_coroutine(recieve, send))
        return return_bytes

    def environ_to_message(self, environ):
        """
        WSGI environ -> ASGI message
        """
        message = {
            'method': environ['REQUEST_METHOD'].upper(),
            'root_path': environ.get('SCRIPT_NAME', ''),
            'path': environ.get('PATH_INFO', ''),
            'query_string': environ.get('QUERY_STRING', '').encode('latin-1'),
            'http_version': environ.get('SERVER_PROTOCOL', 'http/1.0').split('/', 1)[-1],
            'scheme': environ.get('wsgi.url_scheme', 'http'),
        }

        if 'REMOTE_ADDR' in environ and 'REMOTE_PORT' in environ:
            message['client'] = [environ['REMOTE_ADDR'], int(environ['REMOTE_PORT'])]
        if 'SERVER_NAME' in environ and 'SERVER_PORT' in environ:
            message['server'] = [environ['SERVER_NAME'], int(environ['SERVER_PORT'])]

        headers = []
        if environ.get('CONTENT_TYPE'):
            headers.append([b'content-type', environ['CONTENT_TYPE'].encode('latin-1')])
        if environ.get('CONTENT_LENGTH'):
            headers.append([b'content-length', environ['CONTENT_LENGTH'].encode('latin-1')])
        for key, val in environ.items():
            if key.startswith('HTTP_'):
                key_bytes = key[5:].replace('_', '-').upper().encode('latin-1')
                val_bytes = val.encode()
                headers.append([key_bytes, val_bytes])

        return message

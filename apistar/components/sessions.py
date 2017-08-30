import contextlib
import hashlib
import os
import time
import typing

from werkzeug.http import dump_cookie, parse_cookie

from apistar import http
from apistar.interfaces import SessionStore

# TODO: salt from SECRET_KEY.
# TODO: Environment to become a component.
# TODO: 'session_id' as configuration.
# TODO: Metadata, expiry etc...


local_memory_sessions = {}  # type: typing.Dict[str, typing.Dict[str, typing.Any]]


class LocalMemorySessionStore(SessionStore):
    def new(self) -> http.Session:
        session_id = self.generate_key(salt=b'abc')
        return http.Session(session_id=session_id)

    def load(self, session_id: str) -> http.Session:
        try:
            data = local_memory_sessions[session_id]
        except KeyError:
            return self.new()
        return http.Session(session_id=session_id, data=data)

    def save(self, session: http.Session) -> typing.Dict[str, str]:
        headers = {}
        if session.is_new:
            cookie = dump_cookie('session_id', session.session_id)
            headers['set-cookie'] = cookie
        local_memory_sessions[session.session_id] = session.data
        return headers

    def generate_key(self, salt: bytes) -> str:
        return hashlib.sha1(b''.join([
            salt,
            str(time.time()).encode('ascii'),
            os.urandom(30)
        ])).hexdigest()


@contextlib.contextmanager
def get_session(cookie: http.Header,
                store: SessionStore,
                response_headers: http.ResponseHeaders) -> typing.Generator[http.Session, None, None]:
    if cookie:
        cookies = parse_cookie(cookie)
        session_id = cookies.get('session_id')
    else:
        session_id = None

    if session_id is not None:
        session = store.load(session_id)
    else:
        session = store.new()

    try:
        yield session
    finally:
        session_headers = store.save(session)
        response_headers.update(session_headers)

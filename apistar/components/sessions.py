import contextlib
import random
import typing

from werkzeug.http import dump_cookie, parse_cookie

from apistar import http
from apistar.interfaces import SessionStore

local_memory_sessions = {}  # type: typing.Dict[str, typing.Dict[str, typing.Any]]


class LocalMemorySessionStore(SessionStore):
    cookie_name = 'session_id'

    def new(self) -> http.Session:
        session_id = self._generate_key()
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
            cookie = dump_cookie(self.cookie_name, session.session_id)
            headers['set-cookie'] = cookie
        if session.is_new or session.is_modified:
            local_memory_sessions[session.session_id] = session.data
        return headers

    def _generate_key(self) -> str:
        length = 30
        allowed_chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
        urandom = random.SystemRandom()
        return ''.join(urandom.choice(allowed_chars) for i in range(length))


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

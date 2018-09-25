from collections import namedtuple

Position = namedtuple('Position', ['line_no', 'column_no', 'index'])


class ErrorMessage:
    def __init__(self, text, code, index=None, position=None):
        self.text = text
        self.code = code
        self.index = index
        self.position = position

    def __eq__(self, other):
        return (
            self.text == other.text and
            self.code == other.code and
            self.index == other.index and
            self.position == other.position
        )

    def __repr__(self):
        return "%s(%s, code=%s, index=%s, position=%s)" % (
            self.__class__.__name__,
            repr(self.text),
            repr(self.code),
            repr(self.index),
            repr(self.position)
        )


class DecodeError(Exception):
    def __init__(self, messages, summary=None):
        self.messages = messages
        self.summary = summary
        super().__init__(messages)


class ParseError(DecodeError):
    pass


class ValidationError(DecodeError):
    def as_dict(self):
        ret = {}
        for message in self.messages:
            lookup = ret
            if message.index:
                for key in message.index[:-1]:
                    lookup.setdefault(key, {})
                    lookup = lookup[key]
            key = message.index[-1] if message.index else None
            lookup[key] = message.text
        return ret


class ErrorResponse(Exception):
    """
    Raised when a client request results in an error response being returned.
    """
    def __init__(self, title, status_code, content):
        self.title = title
        self.status_code = status_code
        self.content = content


class ClientError(Exception):
    """
    Raised when a client is unable to fulfil an API request.
    """
    def __init__(self, messages):
        self.messages = messages
        super().__init__(messages)

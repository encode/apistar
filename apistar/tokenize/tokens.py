from apistar.exceptions import Position


class Token():
    def __init__(self, value, start_index: int, end_index: int, content=None):
        self._value = value
        self.start_index = start_index
        self.end_index = end_index
        self._content = content

    def get_value(self):
        raise NotImplemented()  # pragma: nocover

    @property
    def start(self):
        return self._get_position(self.start_index)

    @property
    def end(self):
        return self._get_position(self.end_index)

    def lookup_position(self, keys=None):
        token = self
        for key in keys or []:
            token = token[key]
        return token.start

    def lookup_key_position(self, keys):
        token = self
        for key in keys[:-1]:
            token = token[key]
        return token.get_key(keys[-1]).start

    def _get_position(self, index):
        content = self._content[:index + 1]
        lines = content.splitlines()
        line_no = max(len(lines), 1)
        column_no = 1 if not lines else max(len(lines[-1]), 1)
        return Position(line_no, column_no, index)

    def __repr__(self):
        return '%s(%s, %d, %d)' % (
            self.__class__.__name__,
            repr(self._value),
            self.start_index,
            self.end_index
        )

    def __eq__(self, other):
        return (
            self.get_value() == other.get_value() and
            self.start_index == other.start_index and
            self.end_index == other.end_index
        )


class ScalarToken(Token):
    def __hash__(self):
        return hash(self._value)

    def get_value(self):
        return self._value


class DictToken(Token):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._keys = {k._value: k for k in self._value.keys()}
        self._values = {k._value: v for k, v in self._value.items()}

    def get_value(self):
        return {
            key_token.get_value(): value_token.get_value()
            for key_token, value_token in self._value.items()
        }

    def get_key(self, key):
        return self._keys[key]

    def __getitem__(self, key):
        return self._values[key]


class ListToken(Token):
    def get_value(self):
        return [
            token.get_value() for token in self._value
        ]

    def __getitem__(self, key):
        return self._value[key]

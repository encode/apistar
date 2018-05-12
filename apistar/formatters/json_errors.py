from json import JSONEncoder
from json.encoder import encode_basestring, encode_basestring_ascii

import click

INFINITY = float('inf')


def json_errors(value, errors):
    encoder = JSONErrorEncoder(errors=errors, indent=4)
    return encoder.encode(value)


class JSONErrorEncoder(JSONEncoder):
    def __init__(self, *args, **kwargs):
        self.errors = kwargs.pop('errors')
        super().__init__(*args, **kwargs)

    def iterencode(self, o, _one_shot=False):
        if self.check_circular:
            markers = {}
        else:
            markers = None
        if self.ensure_ascii:
            _encoder = encode_basestring_ascii
        else:
            _encoder = encode_basestring

        def floatstr(o, allow_nan=self.allow_nan):
            # Check for specials.  Note that this type of test is processor
            # and/or platform-specific, so do tests which don't depend on the
            # internals.

            if o != o:
                text = 'NaN'
            elif o == INFINITY:
                text = 'Infinity'
            elif o == -INFINITY:
                text = '-Infinity'
            else:
                return float.__repr__(o)

            if not allow_nan:
                raise ValueError(
                    "Out of range float values are not JSON compliant: " +
                    repr(o))

            return text

        _iterencode = _make_iterencode(
            markers, self.default, _encoder, self.indent, floatstr,
            self.key_separator, self.item_separator, self.sort_keys,
            self.skipkeys, _one_shot)
        return _iterencode(o, 0, self.errors)


def _make_iterencode(markers, _default, _encoder, _indent, _floatstr,
                     _key_separator, _item_separator, _sort_keys, _skipkeys, _one_shot):

    if _indent is not None and not isinstance(_indent, str):
        _indent = ' ' * _indent

    def _iterencode_list(lst, _current_indent_level, _errors):
        if not lst:
            yield '[]'
            return
        if markers is not None:
            markerid = id(lst)
            if markerid in markers:
                raise ValueError("Circular reference detected")
            markers[markerid] = lst
        buf = '['
        if _indent is not None:
            _current_indent_level += 1
            newline_indent = '\n' + _indent * _current_indent_level
            separator = _item_separator + newline_indent
            buf += newline_indent
        else:
            newline_indent = None
            separator = _item_separator
        first = True
        current_error = None
        for idx, value in enumerate(lst):
            if first:
                first = False
            else:
                buf = separator
                if current_error and isinstance(current_error, str):
                    buf += click.style('^ ' + current_error, fg='red')
                    buf += '\n' + _indent * _current_indent_level

            current_error = _errors.get(idx)

            if isinstance(value, str):
                yield buf + _encoder(value)
            elif value is None:
                yield buf + 'null'
            elif value is True:
                yield buf + 'true'
            elif value is False:
                yield buf + 'false'
            elif isinstance(value, int):
                # Subclasses of int/float may override __str__, but we still
                # want to encode them as integers/floats in JSON. One example
                # within the standard library is IntEnum.
                yield buf + int.__str__(value)
            elif isinstance(value, float):
                # see comment above for int
                yield buf + _floatstr(value)
            else:
                yield buf
                if isinstance(value, (list, tuple)):
                    chunks = _iterencode_list(value, _current_indent_level, current_error)
                elif isinstance(value, dict):
                    chunks = _iterencode_dict(value, _current_indent_level, current_error)
                else:
                    chunks = _iterencode(value, _current_indent_level, current_error)
                yield from chunks

        if current_error and isinstance(current_error, str):
            yield '\n' + _indent * _current_indent_level
            yield click.style('^ ' + current_error, fg='red')

        if newline_indent is not None:
            _current_indent_level -= 1
            yield '\n' + _indent * _current_indent_level
        yield ']'
        if markers is not None:
            del markers[markerid]

    def _iterencode_dict(dct, _current_indent_level, _errors):
        if not dct:
            yield '{'
            if _errors:
                for key, current_error in _errors.items():
                    if isinstance(current_error, str):
                        yield '\n' + _indent * (_current_indent_level + 1)
                        yield click.style(_encoder(key) + ': ' + current_error, fg='red')
                yield '\n' + _indent * _current_indent_level
            yield '}'
            return
        if markers is not None:
            markerid = id(dct)
            if markerid in markers:
                raise ValueError("Circular reference detected")
            markers[markerid] = dct
        yield '{'
        if _indent is not None:
            _current_indent_level += 1
            newline_indent = '\n' + _indent * _current_indent_level
            item_separator = _item_separator + newline_indent
            yield newline_indent
        else:
            newline_indent = None
            item_separator = _item_separator
        first = True
        if _sort_keys:
            items = sorted(dct.items(), key=lambda kv: kv[0])
        else:
            items = dct.items()

        current_error = None
        current_key = None
        for key, value in items:
            if isinstance(key, str):
                pass
            # JavaScript is weakly typed for these, so it makes sense to
            # also allow them.  Many encoders seem to do something like this.
            elif isinstance(key, float):
                # see comment for int/float in _make_iterencode
                key = _floatstr(key)
            elif key is True:
                key = 'true'
            elif key is False:
                key = 'false'
            elif key is None:
                key = 'null'
            elif isinstance(key, int):
                # see comment for int/float in _make_iterencode
                key = int.__str__(key)
            elif _skipkeys:
                continue
            else:
                raise TypeError('keys must be str, int, float, bool or None, '
                                'not {key.__class__.__name__}')
            if first:
                first = False
            else:
                yield item_separator
                if current_error and isinstance(current_error, str):
                    if current_error.code != 'no_additional_properties':
                        yield ' ' * len('"%s": ' % current_key)
                    yield click.style('^ ' + current_error, fg='red')
                    yield '\n' + _indent * _current_indent_level

            current_error = _errors.get(key)
            current_key = key

            yield _encoder(key)
            yield _key_separator
            if isinstance(value, str):
                yield _encoder(value)
            elif value is None:
                yield 'null'
            elif value is True:
                yield 'true'
            elif value is False:
                yield 'false'
            elif isinstance(value, int):
                # see comment for int/float in _make_iterencode
                yield int.__str__(value)
            elif isinstance(value, float):
                # see comment for int/float in _make_iterencode
                yield _floatstr(value)
            else:
                if isinstance(value, (list, tuple)):
                    chunks = _iterencode_list(value, _current_indent_level, current_error)
                elif isinstance(value, dict):
                    chunks = _iterencode_dict(value, _current_indent_level, current_error)
                else:
                    chunks = _iterencode(value, _current_indent_level, current_error)
                yield from chunks

        if current_error and isinstance(current_error, str):
            yield '\n' + _indent * _current_indent_level
            if current_error.code != 'no_additional_properties':
                yield ' ' * len('"%s": ' % current_key)
            yield click.style('^ ' + current_error, fg='red')

        for key, current_error in _errors.items():
            if key not in dct and isinstance(current_error, str):
                yield '\n' + _indent * _current_indent_level
                yield click.style(_encoder(key) + ': ' + current_error, fg='red')

        if newline_indent is not None:
            _current_indent_level -= 1
            yield '\n' + _indent * _current_indent_level
        yield '}'
        if markers is not None:
            del markers[markerid]

    def _iterencode(o, _current_indent_level, _errors):
        if isinstance(o, str):
            yield _encoder(o)
        elif o is None:
            yield 'null'
        elif o is True:
            yield 'true'
        elif o is False:
            yield 'false'
        elif isinstance(o, int):
            # see comment for int/float in _make_iterencode
            yield int.__str__(o)
        elif isinstance(o, float):
            # see comment for int/float in _make_iterencode
            yield _floatstr(o)
        elif isinstance(o, (list, tuple)):
            yield from _iterencode_list(o, _current_indent_level, _errors)
        elif isinstance(o, dict):
            yield from _iterencode_dict(o, _current_indent_level, _errors)
        else:
            if markers is not None:
                markerid = id(o)
                if markerid in markers:
                    raise ValueError("Circular reference detected")
                markers[markerid] = o
            o = _default(o)
            yield from _iterencode(o, _current_indent_level, _errors)
            if markers is not None:
                del markers[markerid]
    return _iterencode

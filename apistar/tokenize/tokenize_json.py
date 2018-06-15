import re
from json.decoder import JSONDecodeError, JSONDecoder, scanstring

from apistar.tokenize.tokens import DictToken, ListToken, ScalarToken

FLAGS = re.VERBOSE | re.MULTILINE | re.DOTALL
WHITESPACE = re.compile(r'[ \t\n\r]*', FLAGS)
WHITESPACE_STR = ' \t\n\r'
NUMBER_RE = re.compile(
    r'(-?(?:0|[1-9]\d*))(\.\d+)?([eE][-+]?\d+)?',
    (re.VERBOSE | re.MULTILINE | re.DOTALL))


def _TokenizingJSONObject(s_and_end, strict, scan_once,
                          memo, _w=WHITESPACE.match, _ws=WHITESPACE_STR):
    s, end = s_and_end
    pairs = []
    pairs_append = pairs.append
    memo_get = memo.setdefault
    # Use a slice to prevent IndexError from being raised, the following
    # check will raise a more specific ValueError if the string is empty
    nextchar = s[end:end + 1]
    # Normally we expect nextchar == '"'
    if nextchar != '"':
        if nextchar in _ws:
            end = _w(s, end).end()
            nextchar = s[end:end + 1]
        # Trivial empty object
        if nextchar == '}':
            return {}, end + 1
        elif nextchar != '"':
            raise JSONDecodeError(
                "Expecting property name enclosed in double quotes", s, end)
    end += 1
    while True:
        start = end - 1
        key, end = scanstring(s, end, strict)
        key = memo_get(key, key)
        key = ScalarToken(memo_get(key, key), start, end - 1)
        # To skip some function call overhead we optimize the fast paths where
        # the JSON key separator is ": " or just ":".
        if s[end:end + 1] != ':':
            end = _w(s, end).end()
            if s[end:end + 1] != ':':
                raise JSONDecodeError("Expecting ':' delimiter", s, end)
        end += 1

        try:
            if s[end] in _ws:
                end += 1
                if s[end] in _ws:
                    end = _w(s, end + 1).end()
        except IndexError:
            pass

        try:
            value, end = scan_once(s, end)
        except StopIteration as err:
            raise JSONDecodeError("Expecting value", s, err.value) from None
        pairs_append((key, value))
        try:
            nextchar = s[end]
            if nextchar in _ws:
                end = _w(s, end + 1).end()
                nextchar = s[end]
        except IndexError:
            nextchar = ''
        end += 1

        if nextchar == '}':
            break
        elif nextchar != ',':
            raise JSONDecodeError("Expecting ',' delimiter", s, end - 1)
        end = _w(s, end).end()
        nextchar = s[end:end + 1]
        end += 1
        if nextchar != '"':
            raise JSONDecodeError(
                "Expecting property name enclosed in double quotes", s, end - 1)
    return dict(pairs), end


def _make_scanner(context):
    parse_object = _TokenizingJSONObject
    parse_array = context.parse_array
    parse_string = context.parse_string
    match_number = NUMBER_RE.match
    strict = context.strict
    parse_float = context.parse_float
    parse_int = context.parse_int
    memo = context.memo

    def _scan_once(string, idx):
        try:
            nextchar = string[idx]
        except IndexError:
            raise StopIteration(idx) from None

        if nextchar == '"':
            value, end = parse_string(string, idx + 1, strict)
            return ScalarToken(value, idx, end - 1), end
        elif nextchar == '{':
            value, end = parse_object(
                (string, idx + 1), strict,
                _scan_once, memo
            )
            return DictToken(value, idx, end - 1), end
        elif nextchar == '[':
            value, end = parse_array((string, idx + 1), _scan_once)
            return ListToken(value, idx, end - 1), end
        elif nextchar == 'n' and string[idx:idx + 4] == 'null':
            value, end = None, idx + 4
            return ScalarToken(value, idx, end - 1), end
        elif nextchar == 't' and string[idx:idx + 4] == 'true':
            value, end = True, idx + 4
            return ScalarToken(value, idx, end - 1), end
        elif nextchar == 'f' and string[idx:idx + 5] == 'false':
            value, end = False, idx + 5
            return ScalarToken(value, idx, end - 1), end

        m = match_number(string, idx)
        if m is not None:
            integer, frac, exp = m.groups()
            if frac or exp:
                res = parse_float(integer + (frac or '') + (exp or ''))
            else:
                res = parse_int(integer)
            value, end = res, m.end()
            return ScalarToken(value, idx, end - 1), end
        else:
            raise StopIteration(idx)

    def scan_once(string, idx):
        try:
            return _scan_once(string, idx)
        finally:
            memo.clear()

    return scan_once


class _TokenizingDecoder(JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scan_once = _make_scanner(self)


def tokenize_json(content):
    decoder = _TokenizingDecoder()
    return decoder.decode(content)

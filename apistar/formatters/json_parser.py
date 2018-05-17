import re
from json.decoder import JSONDecodeError, JSONDecoder, scanstring

from apistar.formatters.nodes import DictNode, ListNode, LiteralNode

FLAGS = re.VERBOSE | re.MULTILINE | re.DOTALL
WHITESPACE = re.compile(r'[ \t\n\r]*', FLAGS)
WHITESPACE_STR = ' \t\n\r'
NUMBER_RE = re.compile(
    r'(-?(?:0|[1-9]\d*))(\.\d+)?([eE][-+]?\d+)?',
    (re.VERBOSE | re.MULTILINE | re.DOTALL))


def JSONObject(s_and_end, strict, scan_once, object_hook, object_pairs_hook,
               memo=None, _w=WHITESPACE.match, _ws=WHITESPACE_STR):
    s, end = s_and_end
    pairs = []
    pairs_append = pairs.append
    # Backwards compatibility
    if memo is None:
        memo = {}
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
            if object_pairs_hook is not None:
                result = object_pairs_hook(pairs)
                return result, end + 1
            pairs = {}
            if object_hook is not None:
                pairs = object_hook(pairs)
            return pairs, end + 1
        elif nextchar != '"':
            raise JSONDecodeError(
                "Expecting property name enclosed in double quotes", s, end)
    end += 1
    while True:
        key_start = end - 1
        key, end = scanstring(s, end, strict)
        key_end = end
        key = memo_get(key, key)
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
        value.key_start = key_start
        value.key_end = key_end
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
    if object_pairs_hook is not None:
        result = object_pairs_hook(pairs)
        return result, end
    pairs = dict(pairs)
    if object_hook is not None:
        pairs = object_hook(pairs)
    return pairs, end


def make_scanner(context):
    parse_object = JSONObject
    parse_array = context.parse_array
    parse_string = context.parse_string
    match_number = NUMBER_RE.match
    strict = context.strict
    parse_float = context.parse_float
    parse_int = context.parse_int
    parse_constant = context.parse_constant
    object_hook = context.object_hook
    object_pairs_hook = context.object_pairs_hook
    memo = context.memo

    def _scan_once(string, idx):
        try:
            nextchar = string[idx]
        except IndexError:
            raise StopIteration(idx) from None

        if nextchar == '"':
            value, end = parse_string(string, idx + 1, strict)
            return LiteralNode(value, idx, end), end
        elif nextchar == '{':
            value, end = parse_object(
                (string, idx + 1), strict,
                _scan_once, object_hook, object_pairs_hook, memo
            )
            return DictNode(value, idx, end), end
        elif nextchar == '[':
            value, end = parse_array((string, idx + 1), _scan_once)
            return ListNode(value, idx, end), end
        elif nextchar == 'n' and string[idx:idx + 4] == 'null':
            value, end = None, idx + 4
            return LiteralNode(value, idx, end), end
        elif nextchar == 't' and string[idx:idx + 4] == 'true':
            value, end = True, idx + 4
            return LiteralNode(value, idx, end), end
        elif nextchar == 'f' and string[idx:idx + 5] == 'false':
            value, end = False, idx + 5
            return LiteralNode(value, idx, end), end

        m = match_number(string, idx)
        if m is not None:
            integer, frac, exp = m.groups()
            if frac or exp:
                res = parse_float(integer + (frac or '') + (exp or ''))
            else:
                res = parse_int(integer)
            value, end = res, m.end()
            return LiteralNode(value, idx, end), end
        elif nextchar == 'N' and string[idx:idx + 3] == 'NaN':
            value, end = parse_constant('NaN'), idx + 3
            return LiteralNode(value, idx, end), end
        elif nextchar == 'I' and string[idx:idx + 8] == 'Infinity':
            value, end = parse_constant('Infinity'), idx + 8
            return LiteralNode(value, idx, end), end
        elif nextchar == '-' and string[idx:idx + 9] == '-Infinity':
            value, end = parse_constant('-Infinity'), idx + 9
            return LiteralNode(value, idx, end), end
        else:
            raise StopIteration(idx)

    def scan_once(string, idx):
        try:
            return _scan_once(string, idx)
        finally:
            memo.clear()

    return _scan_once


class JSONNodeDecoder(JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scan_once = make_scanner(self)


def parse_json(content):
    decoder = JSONNodeDecoder()
    return decoder.decode(content)

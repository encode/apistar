from typing import List, Union


class Token():
    def __init__(self, value, start: int, end: int):
        self.value = value
        self.start = start
        self.end = end

    def lookup(self, keys: List[Union[str, int]], lookup_property: bool=False) -> 'Token':
        raise NotImplementedError()

    def __repr__(self):
        return '%s(%s, %d, %d)' % (
            self.__class__.__name__,
            repr(self.value),
            self.start,
            self.end
        )

    def __eq__(self, other):
        return (
            self.value == other.value and
            self.start == other.start and
            self.end == other.end
        )


class ScalarToken(Token):
    def lookup(self, keys: List[Union[str, int]], lookup_property: bool=False) -> Token:
        if not keys:
            return self
        raise KeyError(keys[0])

    def __hash__(self):
        return hash(self.value)


class DictToken(Token):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keys = {k.value: k for k in self.value.keys()}
        self.values = {k.value: v for k, v in self.value.items()}

    def lookup(self, keys: List[Union[str, int]], lookup_property: bool=False) -> Token:
        if not keys:
            return self
        elif len(keys) == 1:
            if lookup_property:
                return self.keys[keys[0]]
            else:
                return self.values[keys[0]]
        return self.values[keys[0]].lookup(keys[1:], lookup_property)


class ListToken(Token):
    def lookup(self, keys: List[Union[str, int]], lookup_property: bool=False) -> Token:
        if not keys:
            return self
        elif len(keys) == 1:
            return self.value[keys[0]]
        return self.value[keys[0]].lookup(keys[1:], lookup_property)

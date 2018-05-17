class LiteralNode:
    def __init__(self, value, start, end):
        self.value = value
        self.start = start
        self.end = end
        self.key_start = None
        self.key_end = None

    def __hash__(self):
        return hash(self.value)

    def __repr__(self):
        return repr(self.value)

    def lookup(self, prefix):
        if not prefix:
            return self
        return self[prefix[0]].lookup(prefix[1:])


class DictNode(dict):
    def __init__(self, value, start, end):
        super().__init__(value)
        self.start = start
        self.end = end
        self.key_start = None
        self.key_end = None

    def __repr__(self):
        return repr(dict(self))

    def lookup(self, prefix):
        if not prefix:
            return self
        return self[prefix[0]].lookup(prefix[1:])


class ListNode(list):
    def __init__(self, value, start, end):
        super().__init__(value)
        self.start = start
        self.end = end
        self.key_start = None
        self.key_end = None

    def __repr__(self):
        return repr(list(self))

    def lookup(self, prefix):
        if not prefix:
            return self
        return self[prefix[0]].lookup(prefix[1:])

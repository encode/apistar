import datetime

import pytest

from apistar import exceptions, types, validators
from apistar.formats import BaseFormat

UTC = datetime.timezone.utc


def test_date():
    class Example(types.Type):
        when = validators.Date()

    example = Example({
        'when': '2020-01-01'
    })
    assert example.when == datetime.date(2020, 1, 1)
    assert example['when'] == '2020-01-01'

    example = Example({
        'when': datetime.date(2020, 1, 1)
    })
    assert example.when == datetime.date(2020, 1, 1)
    assert example['when'] == '2020-01-01'

    with pytest.raises(exceptions.ValidationError) as exc:
        Example({'when': 'abc'})
    assert exc.value.detail == {'when': 'Must be a valid date.'}

    with pytest.raises(exceptions.ValidationError) as exc:
        Example({'when': None})
    assert exc.value.detail == {'when': 'May not be null.'}


def test_nullable_date():
    class Example(types.Type):
        when = validators.Date(allow_null=True)

    example = Example({
        'when': None
    })
    assert example.when is None
    assert example['when'] is None


def test_time():
    class Example(types.Type):
        when = validators.Time()

    example = Example({
        'when': '12:00:00'
    })
    assert example.when == datetime.time(12, 0, 0)
    assert example['when'] == '12:00:00'

    example = Example({
        'when': datetime.time(12, 0, 0)
    })
    assert example.when == datetime.time(12, 0, 0)
    assert example['when'] == '12:00:00'

    with pytest.raises(exceptions.ValidationError) as exc:
        Example({'when': 'abc'})
    assert exc.value.detail == {'when': 'Must be a valid time.'}

    with pytest.raises(exceptions.ValidationError) as exc:
        Example({'when': None})
    assert exc.value.detail == {'when': 'May not be null.'}


def test_nullable_time():
    class Example(types.Type):
        when = validators.Time(allow_null=True)

    example = Example({
        'when': None
    })
    assert example.when is None
    assert example['when'] is None


def test_datetime():
    class Example(types.Type):
        when = validators.DateTime()

    example = Example({
        'when': '2020-01-01T12:00:00Z'
    })
    assert example.when == datetime.datetime(2020, 1, 1, 12, 0, 0, tzinfo=UTC)
    assert example['when'] == '2020-01-01T12:00:00Z'

    example = Example({
        'when': datetime.datetime(2020, 1, 1, 12, 0, 0, tzinfo=UTC)
    })
    assert example.when == datetime.datetime(2020, 1, 1, 12, 0, 0, tzinfo=UTC)
    assert example['when'] == '2020-01-01T12:00:00Z'

    with pytest.raises(exceptions.ValidationError) as exc:
        Example({'when': 'abc'})
    assert exc.value.detail == {'when': 'Must be a valid datetime.'}

    with pytest.raises(exceptions.ValidationError) as exc:
        Example({'when': None})
    assert exc.value.detail == {'when': 'May not be null.'}

    example = Example({
        'when': '2020-01-01T12:00:00-02:00'
    })
    tzinfo = datetime.timezone(-datetime.timedelta(hours=2))
    assert example.when == datetime.datetime(2020, 1, 1, 12, 0, 0, tzinfo=tzinfo)
    assert example['when'] == '2020-01-01T12:00:00-02:00'


def test_nullable_datetime():
    class Example(types.Type):
        when = validators.DateTime(allow_null=True)

    example = Example({
        'when': None
    })
    assert example.when is None
    assert example['when'] is None


def test_custom_formatter():
    class Foo:
        def __init__(self, bar):
            self.bar = bar

    class FooFormatter(BaseFormat):
        def is_native_type(self, value):
            return isinstance(value, Foo)

        def to_string(self, value):
            return value.bar

        def validate(self, value):
            if not isinstance(value, str) or not value.startswith('bar_'):
                raise exceptions.ValidationError('Must start with bar_.')
            return Foo(value)

    class Example(types.Type):
        foo = validators.String(formatter=FooFormatter())

    with pytest.raises(exceptions.ValidationError) as exc:
        example = Example({
            'foo': 'foo'
        })
    assert exc.value.detail == {'foo': 'Must start with bar_.'}

    example = Example({'foo': 'bar_foo'})
    assert isinstance(example.foo, Foo)
    assert example.foo.bar == 'bar_foo'
    assert example['foo'] == 'bar_foo'




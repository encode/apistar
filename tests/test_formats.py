import datetime

import pytest

from apistar import exceptions, types, validators

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

    example = Example({
        'when': '2020-01-01T12:00:00-02:00'
    })
    tzinfo = datetime.timezone(-datetime.timedelta(hours=2))
    assert example.when == datetime.datetime(2020, 1, 1, 12, 0, 0, tzinfo=tzinfo)
    assert example['when'] == '2020-01-01T12:00:00-02:00'

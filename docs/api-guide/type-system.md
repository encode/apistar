# Type System

API Star comes with a type system that allows you to express constraints on the
expected inputs and outputs of your interface.

## The `Type` class

Here’s a quick example of what the type system in API Star looks like:

```python
from apistar import types, validators


class Product(types.Type):
    name = validators.String(max_length=100)
    rating = validators.Integer(minimum=1, maximum=5)
    in_stock = validators.Boolean(default=False)
    size = validators.String(enum=['small', 'medium', 'large'])
```

You can use the type system both for validation of incoming request data, and
for serializing outgoing response data.

Invalid data will result in a `ValidationError` being raised.

```python
>>> data = {'name': 't-shirt', 'size': 'big'}
>>> product = Product(data)
apistar.exceptions.ValidationError: {'rating': 'This field is required.', 'size': 'Must be a valid choice.'}
```

Valid data will instantiate a new `Type` instance.

```python
>>> data = {'name': 't-shirt', 'rating': 4, 'size': 'large'}
>>> product = Product(data)
<Product(name='t-shirt', rating=4, in_stock=False, size='large')>
```

You can access the values on a `Type` instance as attributes.

```python
>>> product.name
't-shirt'
```

Or treat a `Type` as a dictionary-like object.

```python
>>> product['rating']:
4
>>> dict(product)
{'name': 't-shirt', 'rating': 4, 'in_stock': False, 'size': 'large'}
```

### Nested types

You can include `Type` classes as fields on other `Type` classes, like so:

```python
class Location(types.Type):
    latitude = validators.Number(maximum=90.0, minimum=-90.0)
    longitude = validators.Number(maximum=180.0, minimum=-180.0)


class Event(types.Type):
    location = Location
    name = validators.String(max_length=100)
```

## Validation

You can use API Star `Type` classes as annotations inside your handler functions.

When you do so, validation will be handled automatically prior to running
the handler function. The type information will also be made available
in the application's API Schema.

```python
def create_product(product: Product):
    # Save a new product record in the database.
    ...

routes = [
    Route('/create_product/', method='POST', handler=create_product)
]
```

## Serialization

You may also want to using the type system for data serialization,
and include the type as a return annotation on handler functions.

Again, doing so will expose the type information to the application's
API Schema, and will help ensure that the information your system
returns matches its documented return types.

```python
import typing


def list_products() -> typing.List[Product]:
    queryset = ...  # Query returning products from a data store.
    return [Product(record) for record in queryset]
```

## Including additional validation

If you have validation rules that cannot be expressed with the default types,
you can include these by subclass the `__init__` method on the class.

This method should return the validated data, or raise a `ValidationError`.

```python
from apistar import exceptions, types, validators


class Organisation(types.Type):
    is_premium = validators.Boolean()
    expiry_date = validators.Date(allow_null=True)

    def __init__(self, *args, **kwargs):
        value = super().__init__(*args, **kwargs)
        if value.is_premium and value.expiry_date is not None:
            message = 'premium organisations should not have any expiry_date set.'
            raise exceptions.ValidationError(message)
        return value
```

## API Reference

The following typesystem types are supported:

### String

Validates string data.

* `default` - A default to be used if a field using this typesystem is missing from a parent `Type`.
* `title` - A title to use in API schemas and documentation.
* `description` - A description to use in API schemas and documentation.
* `max_length` - A maximum valid length for the data.
* `min_length` - A minimum valid length for the data.
* `pattern` - A string value, giving a regular expression that the data must match.
* `enum` - A list of valid strings that the input must match against.
* `format` - An identifier indicating a complex datatype with a string representation. For example `"date"`, to represent an ISO 8601 formatted date string.
* `allow_null` - Indicates if `None` should be considered a valid value. Defaults to `False`. If set to `True` and no default value is specified then default=`None` will be used.

### Number

Validates numeric data.

* `default` - A default to be used if a field using this typesystem is missing from a parent `Type`.
* `title` - A title to use in API schemas and documentation.
* `description` - A description to use in API schemas and documentation.
* `maximum` - A float representing the maximum valid value for the data.
* `minimum` - A float representing the minimum valid value for the data.
* `exclusive_maximum` - `True` for an exclusive maximum limit. Defaults to `False`.
* `exclusive_minimum` - `True` for an exclusive minimum limit. Defaults to `False`.
* `multiple_of` - A float that the data must be strictly divisible by, in order to be valid.
* `enum` - A list of valid numbers that the input must match against.
* `allow_null` - Indicates if `None` should be considered a valid value. Defaults to `False`. If set to `True` and no default value is specified then default=`None` will be used.

### Integer

Validates integer data.

* `default` - A default to be used if a field using this typesystem is missing from a parent `Type`.
* `title` - A title to use in API schemas and documentation.
* `description` - A description to use in API schemas and documentation.
* `maximum` - An int representing the maximum valid value for the data.
* `minimum` - An int representing the minimum valid value for the data.
* `exclusive_maximum` - `True` for an exclusive maximum limit. Defaults to `False`.
* `exclusive_minimum` - `True` for an exclusive minimum limit. Defaults to `False`.
* `multiple_of` - An integer that the data must be strictly divisible by, in order to be valid.
* `enum` - A list of valid numbers that the input must match against.
* `allow_null` - Indicates if `None` should be considered a valid value. Defaults to `False`. If set to `True` and no default value is specified then default=`None` will be used.

### Boolean

Validates boolean input.

* `default` - A default to be used if a field using this typesystem is missing from a parent `Type`.
* `title` - A title to use in API schemas and documentation.
* `description` - A description to use in API schemas and documentation.
* `allow_null` - Indicates if `None` should be considered a valid value. Defaults to `False`. If set to `True` and no default value is specified then default=`None` will be used.

### Object

Validates dictionary input.

* `default` - A default to be used if a field using this typesystem is missing from a parent `Type`.
* `title` - A title to use in API schemas and documentation.
* `description` - A description to use in API schemas and documentation.
* `properties` - A dictionary mapping string key names to child validators.
* `pattern_properties` - A dictionary mapping regex key names to child validators.
* `additional_properties` - `True` if additional properties should be allowed. `None` if additional properties should be discarded. `False` if additional properties should raise errors. Or a validator instance, to type check any additional properties against.
* `min_properties` - An integer indicating the minimum number of properties that may be present. Defaults to `None`.
* `max_properties` - An integer indicating the maximum number of properties that may be present. Defaults to `None`.
* `required` - A list of strings, indicating which properties are required.
* `allow_null` - Indicates if `None` should be considered a valid value. Defaults to `False`. If set to `True` and no default value is specified then default=`None` will be used.

You'll typically want to use the simpler declarative `Type` style for
describing dictionary inputs, but the `Object` validator may be useful if you
need more general purpose validation.

### Array

Validates list input.

* `default` - A default to be used if a field using this typesystem is missing from a parent `Type`.
* `title` - A title to use in API schemas and documentation.
* `description` - A description to use in API schemas and documentation.
* `items` - A validator or a list of validators.
* `additional_items` - Whether additional items past the end of the listed typesystem types are permitted.
* `min_items` - The minimum number of items the array must contain.
* `max_items` - The maximum number of items the array must contain.
* `unique_items` - Whether repeated items are permitted in the array.
* `allow_null` - Indicates if `None` should be considered a valid value. Defaults to `False`. If set to `True` and no default value is specified then default=`None` will be used.

## Formats

The following validators return a native python representation, but can be serialized to strings.

Let's declare a new type to see how they work...

```python
from apistar import types, validators


class Event(types.Type):
    when = validators.DateTime()
    description = validators.String(max_length=100)
```

When accessed as attributes on a type, these validators return the native python value.

```python
>>> data = {'when': '2021-06-15T12:31:38.269545', 'description': 'New customer signup'}
>>> event = Event(data)
>>> event.when
datetime.datetime(2021, 6, 15, 12, 31, 38, 269545)
```

You can also access the serialized string representation if needed.

```python
>>> event['when']
'2021-04-11T12:31:38.269545'
>>> dict(event)
{'when': '2021-04-11T12:31:38.269545', 'description': 'New customer signup'}
```

### Date

* `default` - A default to be used if a field using this typesystem is missing from a parent `Type`.
* `title` - A title to use in API schemas and documentation.
* `description` - A description to use in API schemas and documentation.
* `allow_null` - Indicates if `None` should be considered a valid value. Defaults to `False`.

### Time

* `default` - A default to be used if a field using this typesystem is missing from a parent `Type`.
* `title` - A title to use in API schemas and documentation.
* `description` - A description to use in API schemas and documentation.
* `allow_null` - Indicates if `None` should be considered a valid value. Defaults to `False`.

### DateTime

* `default` - A default to be used if a field using this typesystem is missing from a parent `Type`.
* `title` - A title to use in API schemas and documentation.
* `description` - A description to use in API schemas and documentation.
* `allow_null` - Indicates if `None` should be considered a valid value. Defaults to `False`.

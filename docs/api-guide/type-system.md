# Type System

API Star comes with a type system that allows you to express constraints on the
expected inputs and outputs of your interface.

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

## API Reference

The following typesystem types are supported:

### String

Validates string data.

* `default` - A default to be used if a field using this typesystem is missing from a parent `Object`.
* `max_length` - A maximum valid length for the data.
* `min_length` - A minimum valid length for the data.
* `pattern` - A string or compiled regex that the data must match.
* `format` - An identifier indicating a complex datatype with a string representation. For example `"date"`, to represent an ISO 8601 formatted date string.
* `trim_whitespace` - `True ` if leading and trailing whitespace should be stripped from the data. Defaults to `True`.
* `description` - A description for online documentation

### Number

Validates numeric data.

* `default` - A default to be used if a field using this typesystem is missing from a parent `Object`.
* `maximum` - A float representing the maximum valid value for the data.
* `minimum` - A float representing the minimum valid value for the data.
* `exclusive_maximum` - `True` for an exclusive maximum limit. Defaults to `False`.
* `exclusive_minimum` - `True` for an exclusive minimum limit. Defaults to `False`.
* `multiple_of` - A float that the data must be strictly divisible by, in order to be valid.
* `description` - A description for online documentation

### Integer

Validates integer data.

* `default` - A default to be used if a field using this typesystem is missing from a parent `Object`.
* `maximum` - An int representing the maximum valid value for the data.
* `minimum` - An int representing the minimum valid value for the data.
* `exclusive_maximum` - `True` for an exclusive maximum limit. Defaults to `False`.
* `exclusive_minimum` - `True` for an exclusive minimum limit. Defaults to `False`.
* `multiple_of` - An integer that the data must be strictly divisible by, in order to be valid.
* `description` - A description for online documentation

### Boolean

Validates boolean input.

* `default` - A default to be used if a field using this typesystem is missing from a parent `Object`.
* `description` - A description for online documentation

### Object

Validates dictionary input.

* `default` - A default to be used if a field using this typesystem is missing from a parent `Object`.
* `properties` - A dictionary mapping string key names to typesystem or type values.
* `description` - A description for online documentation

Note that child properties are considered to be required if they do not have a `default` value.

### Array

Validates list input.

* `items` - A typesystem or type or a list of typesystems or types.
* `additional_items` - Whether additional items past the end of the listed typesystem types are permitted.
* `min_items` - The minimum number of items the array must contain.
* `max_items` - The maximum number of items the array must contain.
* `unique_items` - Whether repeated items are permitted in the array.
* `description` - A description for online documentation

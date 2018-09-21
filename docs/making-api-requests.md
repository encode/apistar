# Making API requests

The APIStar client library allows you to make requests to an API, given an API Schema.

Here's an example of how an API request might look:

```shell
$ apistar request listWidgets search=cogwheel --path schema.json
[
    {
        "name": "Small cogwheel.",
        "productId": 24325,
        "inStock": true
    },
    {
        "name": "Large cogwheel.",
        "productId": 24326,
        "inStock": true
    }
]
```

## Configuration

To make an API request you'll normally want to make sure you have an
`apistar.yml` configuration file which references the API schema.

This will save you from having to include the schema path on every request.

```yaml
schema:
    path: schema.json
    format: openapi
```

We can now make the request more simply, as:

```shell
$ apistar request listWidgets search=cogwheel
[
    {
        "name": "Small cogwheel.",
        "productId": 24325,
        "inStock": true
    },
    {
        "name": "Large cogwheel.",
        "productId": 24326,
        "inStock": true
    }
]
```

## Loading a new schema

To start working against a new API you can use the `load` command to download
the schema, and generate a config file for it:

```shell
$ apistar load https://petstore.swagger.io/v2/swagger.json
Downloaded "swagger.json", and created "apistar.yml".
$ apistar request ...
```

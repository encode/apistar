from urllib.parse import quote, urljoin, urlparse

import apistar
from apistar import exceptions, validators
from apistar.client import transports


class Client():
    def __init__(
        self, schema, format=None, encoding=None, auth=None, decoders=None,
        encoders=None, headers=None, session=None, allow_cookies=True
    ):
        self.document = apistar.validate(schema, format=format, encoding=encoding)
        self.transport = self.init_transport(auth, decoders, encoders, headers, session, allow_cookies)

    def init_transport(self, auth=None, decoders=None, encoders=None, headers=None, session=None, allow_cookies=True):
        return transports.HTTPTransport(
            auth=auth,
            decoders=decoders,
            encoders=encoders,
            headers=headers,
            session=session,
            allow_cookies=allow_cookies
        )

    def lookup_operation(self, operation_id: str):
        for item in self.document.walk_links():
            if item.link.name == operation_id:
                return item.link
        text = 'Operation ID "%s" not found in schema.' % operation_id
        message = exceptions.ErrorMessage(text=text, code='invalid-operation')
        raise exceptions.ClientError(messages=[message])

    def get_url(self, link, params):
        url = urljoin(self.document.url, link.url)

        scheme = urlparse(url).scheme.lower()

        if not scheme:
            text = "URL missing scheme '%s'." % url
            message = exceptions.ErrorMessage(text=text, code='invalid-url')
            raise exceptions.ClientError(messages=[message])

        if scheme not in self.transport.schemes:
            text = "Unsupported URL scheme '%s'." % scheme
            message = exceptions.ErrorMessage(text=text, code='invalid-url')
            raise exceptions.ClientError(messages=[message])

        for field in link.get_path_fields():
            value = str(params[field.name])
            if '{%s}' % field.name in url:
                url = url.replace('{%s}' % field.name, quote(value, safe=''))
            elif '{+%s}' % field.name in url:
                url = url.replace('{+%s}' % field.name, quote(value, safe='/'))

        return url

    def get_query_params(self, link, params):
        return {
            field.name: params[field.name]
            for field in link.get_query_fields()
            if field.name in params
        }

    def get_content_and_encoding(self, link, params):
        body_field = link.get_body_field()
        if body_field and body_field.name in params:
            return (params[body_field.name], link.encoding)
        return (None, None)

    def request(self, operation_id: str, **params):
        link = self.lookup_operation(operation_id)

        validator = validators.Object(
            properties={field.name: validators.Any() for field in link.fields},
            required=[field.name for field in link.fields if field.required],
            additional_properties=False
        )
        try:
            validator.validate(params)
        except exceptions.ValidationError as exc:
            raise exceptions.ClientError(messages=exc.messages) from None

        method = link.method
        url = self.get_url(link, params)
        query_params = self.get_query_params(link, params)
        (content, encoding) = self.get_content_and_encoding(link, params)

        return self.transport.send(
            method,
            url,
            query_params=query_params,
            content=content,
            encoding=encoding
        )

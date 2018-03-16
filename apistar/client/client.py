from urllib.parse import quote, urljoin, urlparse

from apistar import exceptions, validators
from apistar.client import transports


class Client():
    def __init__(self, document, auth=None, decoders=None, headers=None, session=None):
        self.document = document
        self.transport = self.init_transport(auth, decoders, headers, session)

    def init_transport(self, auth=None, decoders=None, headers=None, session=None):
        return transports.HTTPTransport(
            auth=auth,
            decoders=decoders,
            headers=headers,
            session=session
        )

    def lookup_link(self, name: str):
        for item in self.document.walk_links():
            if item.name == name:
                return item.link
        raise exceptions.RequestError('Link "%s" not found in document.' % name)

    def get_url(self, link, params):
        url = urljoin(self.document.url, link.url)

        scheme = urlparse(url).scheme.lower()

        if not scheme:
            raise exceptions.RequestError("URL missing scheme '%s'." % url)

        if scheme not in self.transport.schemes:
            raise exceptions.RequestError("Unsupported URL scheme '%s'." % scheme)

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

    def request(self, name: str, **params):
        link = self.lookup_link(name)

        validator = validators.Object(
            properties={field.name: validators.Any() for field in link.fields},
            required=[field.name for field in link.fields if field.required],
            additional_properties=False
        )
        validator.validate(params)

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

from urllib.parse import urljoin, urlparse

from apistar import codecs, exceptions, types
from apistar.client import transports


class Client():
    def __init__(self, document, decoders=None, auth=None, headers=None, session=None):
        self.document = document
        self.transport = self.get_transport(decoders, auth, headers, session)

    def get_transport(self, decoders=None, auth=None, headers=None, session=None):
        return transports.HTTPTransport(
            decoders=decoders,
            auth=auth,
            headers=headers,
            session=session
        )

    def validate_url(self, url):
        components = urlparse(url)
        scheme = components.scheme.lower()
        netloc = components.netloc

        if not scheme:
            raise exceptions.RequestError("URL missing scheme '%s'." % url)

        if not netloc:
            raise exceptions.RequestError("URL missing hostname '%s'." % url)

        if scheme not in self.transport.schemes:
            raise exceptions.RequestError("Unsupported URL scheme '%s'." % scheme)

    def lookup_link(self, name: str):
        for item in self.document.walk_links():
            if item.name == name:
                return item.link
        raise exceptions.RequestError('Link "%s" not found in document.' % name)

    def request(self, name: str, **params):
        link = self.lookup_link(name)
        validator = types.Object(
            properties={field.name: types.Any() for field in link.fields},
            required=[field.name for field in link.fields if field.required],
            additional_properties=False
        )
        validator.validate(params)

        url = urljoin(self.document.url, link.url)
        self.validate_url(url)
        return self.transport.transition(url, link, params=params)

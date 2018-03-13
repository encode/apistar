from apistar import codecs, exceptions
from apistar.client import transports
from coreapi.utils import determine_transport


class Client():
    def __init__(self, document, decoders=None, auth=None, headers=None, session=None):
        self.document = document
        self.decoders = self.get_decoders(decoders)
        self.transports = self.get_transports(auth, headers, session)

    def get_decoders(self, decoders=None):
        if decoders is None:
            return [
                codecs.JSONCodec(),
                codecs.TextCodec(),
                codecs.DownloadCodec()
            ]
        return list(decoders)

    def get_transports(self, auth=None, headers=None, session=None):
        return [
            transports.HTTPTransport(
                auth=auth,
                headers=headers,
                session=session
            )
        ]

    def request(self, name, params=None):
        if params is None:
            params = {}

        link = self.document.lookup_link(name)
        validator = types.Object(
            items={field.name: types.Any() for field in link.fields},
            required=[field.name for field in link.fields if field.required],
            additional_items=False
        )
        validator.validate(params)

        transport = determine_transport(self.transports, link.url)
        return transport.transition(link, self.decoders, params=params)

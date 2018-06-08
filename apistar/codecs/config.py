import yaml

from apistar import validators
from apistar.codecs import BaseCodec
from apistar.exceptions import ParseError

CONFIG = validators.Object(
    properties=[
        ('schema', validators.Object(
            properties=[
                ('path', validators.String()),
                ('format', validators.String(enum=['openapi', 'swagger'])),
            ],
            additional_properties=False,
            required=['path', 'format']
        )),
        ('docs', validators.Object(
            properties=[
                ('theme', validators.String(enum=['apistar', 'redoc', 'swaggerui'])),
            ],
            additional_properties=False,
        ))
    ],
    additional_properties=False,
    required=['schema'],
)


class ConfigCodec(BaseCodec):
    media_type = 'application/x-yaml'
    format = 'apistar'

    def decode(self, bytestring, **options):
        content = bytestring.decode('utf-8')
        content = content.strip()
        if not content:
            raise ParseError(
                message='No content.',
                short_message='No content.',
                pos=0,
                lineno=1,
                colno=1
            )

        try:
            data = yaml.safe_load(content)
        except (yaml.scanner.ScannerError, yaml.parser.ParserError) as exc:
            if not hasattr(exc, 'index'):
                index = 0
                lineno = 1
                colno = 1
            else:
                index = exc.index
                lineno = exc.line
                colno = exc.column
            raise ParseError(
                message='% at line %d column %d' % (exc.problem, exc.problem_mark.line, exc.problem_mark.column),
                short_message=exc.problem,
                pos=index,
                lineno=lineno,
                colno=colno
            ) from None
        except ValueError as exc:
            raise ParseError('Malformed YAML. %s' % exc) from None

        CONFIG.validate(data)
        return data

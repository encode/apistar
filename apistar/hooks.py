from apistar import Settings, exceptions, http
from apistar.interfaces import Injector
from apistar.renderers import DEFAULT_RENDERERS, negotiate_renderer
from apistar.types import Handler, ReturnValue


def check_permissions(handler: Handler,
                      injector: Injector,
                      settings: Settings) -> None:
    """
    Ensure that any configured permissions are met.

    Used in the default `BEFORE_REQUEST` configuration.
    """
    default_permissions = settings.get('PERMISSIONS', None)
    permissions = getattr(handler, 'permissions', default_permissions)
    if permissions is None:
        return

    for permission in permissions:
        if not injector.run(permission.has_permission):
            raise exceptions.Forbidden()


async def check_permissions_async(handler: Handler,
                                  injector: Injector,
                                  settings: Settings):
    """
    An async variant of 'check_permissions'.
    """
    default_permissions = settings.get('PERMISSIONS', None)
    permissions = getattr(handler, 'permissions', default_permissions)
    if permissions is None:
        return

    for permission in permissions:
        if not await injector.run_async(permission.has_permission):
            raise exceptions.Forbidden()


def render_response(handler: Handler,
                    injector: Injector,
                    settings: Settings,
                    accept: http.Header,
                    ret: ReturnValue) -> http.Response:
    """
    Render a response, using content negotiation to determine an
    appropriate renderer.

    Used in the default `BEFORE_REQUEST` configuration.
    """
    if isinstance(ret, http.Response):
        data, status, headers, content_type = ret
        if content_type is not None or (status >= 300 and status <= 399):
            return ret
    else:
        data, status, headers, content_type = ret, 200, {}, None

    if data is None or data == b'':
        content = b''
        content_type = None
    else:
        default_renderers = settings.get('RENDERERS', DEFAULT_RENDERERS)
        renderers = getattr(handler, 'renderers', default_renderers)
        renderer = negotiate_renderer(accept, renderers)
        if renderer is None:
            raise exceptions.NotAcceptable()
        content = injector.run(renderer.render, {'response_data': data})
        if isinstance(content, http.Response):
            return content
        content_type = renderer.get_content_type()

    if not content and status == 200:
        status = 204
        content_type = None

    return http.Response(content, status, headers, content_type)

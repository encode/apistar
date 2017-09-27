"""
Type annotations that may be used in handler functions.
"""
import typing

from apistar import typesystem
from apistar.core import Command, Include, Route

# URL & Command Routing
# =====================

# The handler and kwargs associated with a URL lookup or parsed CLI arguments.

Handler = typing.TypeVar('Handler')
KeywordArgs = typing.Dict[str, typing.Any]
HandlerLookup = typing.Tuple[Handler, KeywordArgs]


# HTTP environment
# ================

# The raw information for an incoming HTTP request, either as a WSGI
# environment, or using the Uvicorn Messaging Interface.

WSGIEnviron = typing.NewType('WSGIEnviron', dict)
UMIMessage = typing.NewType('UMIMessage', dict)
UMIChannels = typing.NewType('UMIChannels', dict)


# App config
# ==========

# Used for the 'routes' configuration of an app.

RouteConfig = typing.Sequence[typing.Union[Route, Include]]
RouteConfig.__name__ = 'RouteConfig'


# Used for the 'commands' configuration of an app.

CommandConfig = typing.Sequence[Command]
CommandConfig.__name__ = 'CommandConfig'


# Used for the 'settings' configuration of an app.

Settings = typing.NewType('Settings', dict)


# Dependency Injection
# ====================

# These types may be used to access meta-information about the parameter
# that a component is being injected into. These allow for behavior such
# as components that make a lookup based on the parameter name used.

ParamName = typing.NewType('ParamName', str)
ParamAnnotation = typing.NewType('ParamAnnotation', type)
ReturnValue = typing.TypeVar('ReturnValue')


# Routing
# =======

# A string subclass that may be used for wildcard-matching URL kwargs,
# unlike the default match which may not include the '/' character.

class PathWildcard(typesystem.String):
    pass

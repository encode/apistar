import sys
import typing

from apistar import commands, exceptions
from apistar.components import commandline, console, dependency
from apistar.core import Command, Component
from apistar.interfaces import App, CommandLineClient, Console, Injector
from apistar.types import CommandConfig, KeywordArgs, RouteConfig, Settings


class CliApp(App):
    INJECTOR_CLS = dependency.DependencyInjector

    BUILTIN_COMMANDS = [
        Command('new', commands.new),
    ]

    BUILTIN_COMPONENTS = [
        Component(CommandLineClient, init=commandline.ArgParseCommandLineClient),
        Component(Console, init=console.PrintConsole)
    ]

    def __init__(self,
                 routes: RouteConfig=None,
                 commands: CommandConfig=None,
                 components: typing.List[Component]=None,
                 settings: typing.Dict[str, typing.Any]=None) -> None:
        if routes is None:
            routes = []
        if commands is None:
            commands = []
        if components is None:
            components = []
        if settings is None:
            settings = {}

        commands = [*self.BUILTIN_COMMANDS, *commands]
        components = [*self.BUILTIN_COMPONENTS, *components]

        initial_state = {
            RouteConfig: routes,
            CommandConfig: commands,
            Settings: settings,
            App: self,
        }

        self.components, self.preloaded_state = self.preload_components(
            component_config=components,
            initial_state=initial_state
        )

        # Setup everything that we need in order to run `self.main()`.
        self.commandline = self.preloaded_state[CommandLineClient]
        self.console = self.preloaded_state[Console]
        self.cli_injector = self.create_cli_injector()

    def preload_components(self,
                           component_config: typing.List[Component],
                           initial_state: typing.Dict[type, typing.Any]) -> typing.Tuple[
                                                                                typing.Dict[type, typing.Callable],
                                                                                typing.Dict[type, typing.Any]
                                                                            ]:
        """
        Create any components that can be preloaded at the point of
        instantiating the app. This ensures that the dependency injection
        will not need to re-create these on every incoming request or
        command-line invocation.

        Args:
            components: The components that have been configured for this app.
            initial_state: The initial state that has been configured for this app.

        Return:
            A tuple of the components that could not be preloaded,
            and the initial state, which may include preloaded components.
        """
        components = {
            cls: init for cls, init, preload in component_config
        }
        should_preload = {
            cls: preload for cls, init, preload in component_config
        }

        injector = self.INJECTOR_CLS(components, initial_state)

        for cls, func in list(components.items()):
            if not should_preload[cls]:
                continue

            try:
                component = injector.run(func)
            except exceptions.CouldNotResolveDependency:
                continue
            del components[cls]
            initial_state[cls] = component
            injector = self.INJECTOR_CLS(components, initial_state)

        return (components, initial_state)

    def create_cli_injector(self) -> Injector:
        """
        Create the dependency injector for running handlers in response to
        command-line invocation.

        Args:
            components: Any components that are created per-request.
            initial_state: Any preloaded components and other initial state.
        """
        return self.INJECTOR_CLS(
            components=self.components,
            initial_state=self.preloaded_state,
            required_state={
                KeywordArgs: 'kwargs',
            },
            resolvers=[dependency.CliResolver()]
        )

    def main(self,
             args: typing.Sequence[str]=None,
             standalone_mode: bool=True):
        if args is None:  # pragma: nocover
            args = sys.argv[1:]

        state = {}
        try:
            handler, kwargs = self.commandline.parse(args)
            state['kwargs'] = kwargs
            ret = self.cli_injector.run_all([handler], state=state)
        except exceptions.CommandLineExit as exc:
            ret = exc.message
        except exceptions.CommandLineError as exc:
            if standalone_mode:  # pragma: nocover
                sys.stderr.write('Error: %s\n' % exc)
                sys.exit(exc.exit_code)
            raise
        except (EOFError, KeyboardInterrupt):  # pragma: nocover
            sys.stderr.write('Aborted!\n')
            sys.exit(1)

        if standalone_mode and ret is not None:  # pragma: nocover
            self.console.echo(ret)
        if not standalone_mode:
            return ret

    def reverse_url(self, identifier: str, **values) -> str:
        msg = "'%s' does not support 'reverse_url'" % self.__class__.__name__
        raise NotImplementedError(msg)

    def render_template(self, template_name: str, **context) -> str:
        msg = "'%s' does not support 'render_template'" % self.__class__.__name__
        raise NotImplementedError(msg)

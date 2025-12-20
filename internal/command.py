"""VIM-like command"""
# pylint: disable=broad-exception-caught

import curses
from shlex import split
from typing import Callable
from lymia.data import ReturnType, status
from lymia.forms import Text

class Command:
    """Commands"""

    def __init__(self) -> None:
        self._buffer = Text("")
        self._cmd: dict[
            str, Callable[[curses.window, list[str]], ReturnType]
        ] = {}
        self._screen: curses.window
        self._helps: dict[str, str] = {}
        self._alias: dict[str, list[str]] = {}

    def add_command(
        self, *value: str, help: str = ""
    ):  # pylint: disable=redefined-builtin
        """Add command"""

        def inner(fn: Callable[[curses.window, list[str]], ReturnType]):
            alias = value[0]
            self._alias[alias] = []
            self._helps[alias] = help or fn.__doc__ or ""
            self._cmd[alias] = fn

            for v in value[1:]:
                self._alias[alias].append(v)
                self._cmd[v] = fn
            return fn

        return inner

    @property
    def alias(self):
        """Aliases"""
        return self._alias.copy()

    @property
    def helplist(self):
        """Help list"""
        return self._helps.copy()

    @property
    def cmds(self):
        """Commands"""
        return self._cmd.copy()

    def use_screen(self, screen: curses.window):
        """Give this class a screen!"""
        self._screen = screen

    @property
    def buffer(self):
        """buffer form"""
        return self._buffer

    def call(self) -> ReturnType:
        """Call appropriate function"""
        try:
            args = split(self._buffer.value)
        except ValueError as exc:
            status.set(f"Error: {exc!s}")
            return ReturnType.ERR
        base = args[0] if len(args) >= 1 else ""
        fn = self._cmd.get(base, None)

        if not base:
            return ReturnType.CONTINUE
        if not fn:
            try:
                status.set(f"Command {base} is not found")
                return ReturnType.ERR
            except IndexError:
                return ReturnType.CONTINUE
        return fn(self._screen, args[1:])


def show_help(screen: curses.window, _):
    """Show help"""
    screen.box()
    for index, (cmd, hs) in enumerate(command.helplist.items()):
        alias = command.alias.get(cmd, None)
        alias_str = ""
        if alias:
            alias_str = f" (alias: {' ,'.join(alias)})"
        if not hs:
            hs = "(undocumented)"
        screen.addstr(index + 1, 1, f"[{cmd}] -> {hs}{alias_str}")


def show_config(screen: curses.window, state: dict[str, str]):
    """Show config"""
    screen.box()
    for index, (key, value) in enumerate(state.items()):
        screen.addstr(index + 1, 1, f"{key} = {value!r}")


command = Command()


# @command.add_command("q")
# def q(_, state: WindowState, *__):
#     """Quit"""
#     if state.popup:
#         state.reset_popup()
#         return ReturnType.CONTINUE
#     return ReturnType.EXIT

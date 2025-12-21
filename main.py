#!/usr/bin/env python3
"""RenVIA"""
from os import stat
from sys import argv
from curses import window
import curses
import sys
from internal.history import HistoryTree
from internal.buffer import Buffer
from internal.cursor import Cursor
from internal.modes import Modes
from internal.utils import set_cursor
from internal import STATE, Basic, use_mice

from internal.editor import DebugState, EditorState, EditorView
from internal.modes.normal import NormalMode
from internal.modes.helpmode import HelpMode
from lymia import Panel, ReturnInfo, Scene, run, ReturnType
from lymia.data import SceneResult, _StatusInfo as StatusInfo
from lymia.environment import Theme
from lymia.utils import prepare_windowed


theme = Theme(2, Basic())

MAX_SIZE = 1024 * 1024 * 1  # 1 MiB

HELP_TEXT = """\
Normal Mode:
[q] -> quit
[i] -> Edit mode
[a] -> Edit mode
[Up/Left/Right/Down] -> Navigation
[x] -> Remove current character
[0] -> Jump to 0th character in this line
[$] -> Jump to last character in this line
[u] -> Undo
[U] -> Redo
[w] -> Write to disk
[h] -> Help
[g] -> Jump to start line
[G] -> Jump to last line
[l] -> Toggle mouse capturing (current={mice})
[;] -> Toggle mouse custom signals (may overlap with some keys) (current={naive})

Edit Mode:
[ESC] -> Return to Normal
"""

DEBUG_TEMPLATE = """\
Debug msg    : {msg}
Input key    : {key}
Cursor pos   : ({col}, {row})
Cursor style : ({cursor_style}@{cursor_visibility})
Term size    : ({width}x{height})
Buffer lines : {sizes}
Mode name    : {name}
"""


def render_line(data: str, maxsize: int, shift: int = 0):
    """Render line"""
    shift = max(shift, 0)
    ln = len(data)
    # If shift is beyond the end, return an all-space string quickly.
    if shift >= ln:
        return " " * maxsize

    end = shift + maxsize
    chunk = data[shift:end]
    clen = len(chunk)
    if clen == maxsize:
        return chunk
    return chunk + (" " * (maxsize - clen))


class Root(Scene):
    """RenVIA"""

    use_default_color = True
    use_mouse = False

    def __init__(self, filename: str) -> None:
        super().__init__()
        self._buffer = Buffer(filename)  # type: ignore
        self._cursor = Cursor(0, 0, 0)
        self._status = StatusInfo()
        self._status.set("")
        self._debug: DebugState = DebugState(StatusInfo(),
                                             0,
                                             0,
                                             0,
                                             0,
                                             0,
                                             0,
                                             0,
                                             0,
                                             False,
                                             None)  # type: ignore
        self._mode = NormalMode()
        self._editor = EditorState(
            self._cursor,
            self._buffer,
            HistoryTree(),
            self._status,
            EditorView(0, 0, 0, 0),
            self._debug,
            [self._mode],
        )
        self._reserved_lines = 2
        self._ctype = 2
        self._escd = curses.get_escdelay()
        self._override = True
        self._moverow = 0
        self._movecol = 0
        self._panels: dict[str, Panel | None] = {}

    def _draw_help(self, ren: window, _):
        ren.erase()
        _, width = ren.getmaxyx()
        ren.box()
        for index, line in enumerate(HELP_TEXT.splitlines(), 1):
            ren.addnstr(
                index,
                1,
                line.format(mice=STATE["use_mice"], naive=STATE["use_naive_mice"]),
                width - 1,
            )

    def update_panels(self):
        for panel in self._panels.values():
            if not panel:
                continue
            if panel.visible:
                panel.draw()

    def _draw_debug(self, ren: window, _):
        ren.erase()
        ren.box()
        tmp = {
            "msg": self._debug.status.get(),
            "key": self._debug.key,
            "col": self._cursor.col,
            "row": self._cursor.row,
            "cursor_style": self._mode.curs_style,
            "cursor_visibility": self._mode.term_vis,
            "width": self.width,
            "height": self.height,
            "sizes": self._buffer.size,
            "name": type(self._mode).__name__,
        }
        msg = DEBUG_TEMPLATE.format(**tmp)
        for index, line in enumerate(msg.splitlines(), 1):
            try:
                ren.addstr(index, 1, line)
            except curses.error:
                pass

    def init_help(self):
        """Draw help mode"""
        width, height = self.term_size
        res = self._reserved_lines

        self._panels["help"] = Panel(
            height - res - 4, width - 6, 1, 3, callback=self._draw_help
        )

    def draw_editor(self):
        """Draw the editor"""
        ren = self._screen
        width, height = self.term_size
        self._editor.window.term_width = width
        self._editor.window.term_height = height
        res = self._reserved_lines
        bmaxh = self._buffer.size
        crow = self._cursor.row
        if bmaxh != 0:
            shift = self._cursor.col - width if self._cursor.col > width else 0
            minh, maxh = prepare_windowed(self._cursor.row, height - res)
            if self._cursor.col > self._buffer.sizeof_line(self._cursor.row):
                self._cursor.col = max(
                    self._buffer.sizeof_line(self._cursor.row) - 1, 0
                )

            if maxh > bmaxh:
                minh = max(minh - (maxh - bmaxh), 0)
                maxh = bmaxh
            self._editor.window.start = minh
            self._editor.window.end = maxh
            crow = self._cursor.row - minh
            for index, relindex in enumerate(range(minh, maxh)):
                style = 0
                if index < (height - self._reserved_lines):
                    try:
                        ren.addnstr(
                            index,
                            0,
                            render_line(self._buffer[relindex], width - 1, shift),
                            width,
                            style,
                        )
                    except IndexError:
                        self._debug.status.set(f"[{relindex} -> {bmaxh}]")

        if (height - res) > bmaxh:
            if bmaxh == 0:
                bmaxh = 1
            for i in range((bmaxh), (height - res)):
                ren.addstr(max(i, 1), 0, "~", Basic.UNCOVERED.pair())
        self._moverow = min(crow, height - res - 1)
        self._movecol = max(min(self._cursor.col, width - 1), 0)

    def deferred_op(self):
        width, height = self.term_size
        res = self._reserved_lines
        row = self._moverow
        col = self._movecol
        try:
            self._screen.move(self._moverow, self._movecol)
        except curses.error:
            self._debug.status.set(
                f"Row={row} [{height - res - 1}], Col={col} [{width - 1}]"
            )

    def draw(self) -> None | ReturnType:
        width, height = self.term_size
        ren = self._screen

        fname = self._buffer.filename + ("*" if self._buffer.dirty else "")
        fst = f" | {self._status.get()}" if self._status.get() != "" else ""
        filestatus = fname + fst
        ren.addnstr(
            height - 2, 0, f"{filestatus:{width}}", width, self._mode.theme.pair()
        )
        # status.set(
        #     f"Row: {self._cursor.row} | Col: {self._cursor.col} | Buffer: {self._buffer.size} | Cursor: {self._mode.curs_style}/{self._mode.term_vis} | Key: {self._lastkey} | Details: {self._debug}"
        # )
        self.update_panels()
        self.show_status()
        self.draw_editor()

    def _check_bufferline(self, nextline: int):
        ccol = self._cursor.col
        sizeof = self._buffer.sizeof_line(nextline)
        self._debug.status.set(f"{ccol} [{sizeof - 1}]")
        if ccol > sizeof:
            self._cursor.col = sizeof

    def init(self, stdscr: window):
        super().init(stdscr)
        curses.set_escdelay(1)
        if self.use_mouse:
            use_mice()
        self._mode.on_enter(self._editor)
        width = 64
        self._panels["debug"] = Panel(
            DEBUG_TEMPLATE.count("\n") + 2, width, 0, self.width - width - 1, self._draw_debug
        )
        self._debug.panel = self._panels['debug']
        if self._debug.show:
            self._panels["debug"].show()

    def on_unmount(self):
        for panel in self._panels.values():
            if panel:
                panel.hide()
        set_cursor(0)

    def keymap_override(self, key: int) -> ReturnType:
        ret: ReturnType | ReturnInfo[Modes] = self._mode.handle_key(key, self._editor)
        if isinstance(ret, ReturnType):
            return ret
        if ret.type != ReturnType.OVERRIDE:
            self._debug.status.set("Unknown receiver!")
            return ReturnType.ERR
        if not isinstance(ret.additional_info, Modes):
            raise TypeError(
                "Context switching failed,"
                f" expected Modes-subclasses, got {type(ret.additional_info)}"
            )
        if isinstance(self._mode, HelpMode):  # on exit
            self._panels["help"] = None
        self._mode.on_exit(self._editor)
        self._mode = ret.additional_info
        self._editor.mode[0] = self._mode

        if isinstance(self._mode, HelpMode):  # on enter
            self.init_help()
        return self._mode.on_enter(self._editor)

    def handle_key(self, key: int) -> ReturnType | SceneResult:
        self._debug.key = key
        self._status.set("")
        return super().handle_key(key)


def init():
    """init"""
    filename = "untitled.txt" if len(argv) == 1 else argv[1]
    try:
        st = stat(filename)
        if st.st_size > MAX_SIZE:
            print(f"File {filename} must not be bigger than 1MB")
            sys.exit(1)
    except FileNotFoundError:
        pass
    return Root(filename), theme


if __name__ == "__main__":
    run(init)

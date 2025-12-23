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
from internal.command import command

from internal.editor import DebugState, EditorState, EditorView, Selection
from internal.modes.normal import NormalMode
from internal.modes.helpmode import HelpMode
from lymia import Panel, ReturnInfo, Scene, run, ReturnType
from lymia.data import SceneResult, _StatusInfo as StatusInfo
from lymia.environment import Theme
from lymia.utils import prepare_windowed
from collections import OrderedDict


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
        self._debug: DebugState = DebugState(
            StatusInfo(), 0, 0, 0, 0, 0, 0, 0, 0, False, None # type: ignore
        )  # type: ignore
        self._mode = NormalMode()
        self._editor = EditorState(
            self._cursor,
            self._buffer,
            HistoryTree(),
            self._status,
            EditorView(0, 0, 0, 0),
            self._debug,
            [self._mode],
            Selection(0, 0, 0, 0),
        )
        self._reserved_lines = 2
        self._ctype = 2
        self._escd = curses.get_escdelay()
        self._override = True
        self._moverow = 0
        self._movecol = 0
        self._panels: dict[str, Panel | None] = {}
        # Render cache: maps (line, maxsize, shift) -> rendered string
        self._render_cache: "OrderedDict[tuple, str]" = OrderedDict()
        self._render_cache_limit = 2048

    def _render_cached(self, line: str, maxsize: int, shift: int) -> str:
        """Return cached rendered line or compute and cache it.

        Cache key uses the line content, maxsize and shift so changes
        to a line automatically miss the cache when the string differs.
        """
        key = (line, maxsize, shift)
        cache = self._render_cache
        try:
            val = cache.pop(key)
            # Move to end (most-recently used)
            cache[key] = val
            return val
        except KeyError:
            rendered = render_line(line, maxsize, shift)
            cache[key] = rendered
            if len(cache) > self._render_cache_limit:
                cache.popitem(last=False)
            return rendered

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
        editor = self._editor
        editor.window.term_width = width
        editor.window.term_height = height
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
            editor.window.start = minh
            editor.window.end = maxh
            crow = self._cursor.row - minh
            for index, relindex in enumerate(range(minh, maxh)):
                if index < (height - self._reserved_lines):
                    try:
                        buffer_line = self._buffer[relindex]
                        # Delegate selection-aware line rendering to helper
                        self._draw_line_with_selection(
                            ren, index, relindex, buffer_line, editor, shift, width
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

    def _draw_line_with_selection(
        self, ren, index: int, relindex: int, buffer_line: str, editor, shift: int, width: int
    ):
        """Draw a single line with selection highlighting when active.

        Parameters mirror the local variables from draw_editor.
        """
        # If there's no active selection, render normally
        if not editor.selection:
            try:
                rendered = self._render_cached(buffer_line, width - 1, shift)
                ren.addnstr(index, 0, rendered, width, 0)
            except curses.error:
                pass
            return

        # Selection is active: compute selection bounds
        s = editor.selection
        # Clamp rows/cols similar to Selection.slice
        buf_len = len(self._buffer)
        sr = max(0, min(s.start_row, buf_len - 1))
        er = max(0, min(s.end_row, buf_len - 1))
        sc = max(0, s.start_col)
        ec = max(0, s.end_col)

        # Same-line selection
        if sr == er:
            # Only highlight when this line is the selected line
            line_len = self._buffer.sizeof_line(sr)
            left = min(sc, ec, line_len)
            right = min(max(sc, ec), line_len)
            if relindex != sr:
                try:
                    ren.addnstr(
                        index,
                        0,
                        render_line(buffer_line, width - 1, shift),
                        width,
                        0,
                    )
                except curses.error:
                    pass
                return

            # Render visible window and then split into prefix/selected/suffix
            full = self._render_cached(buffer_line, width - 1, shift)
            vis_left = max(left, shift) - shift
            vis_right = min(right, shift + (width - 1)) - shift
            vis_left = max(0, min(vis_left, width - 1))
            vis_right = max(0, min(vis_right, width - 1))
            if vis_left >= vis_right:
                try:
                    ren.addnstr(index, 0, full, width, 0)
                except curses.error:
                    pass
                return

            try:
                if vis_left > 0:
                    ren.addnstr(
                        index,
                        0,
                        full[:vis_left],
                        vis_left,
                        0,
                    )
                ren.addnstr(
                    index,
                    vis_left,
                    full[vis_left:vis_right],
                    vis_right - vis_left,
                    Basic.FNBUFFER_SELECTION.pair(),
                )
                if vis_right < (width - 1):
                    ren.addnstr(
                        index,
                        vis_right,
                        full[vis_right:],
                        width - vis_right,
                        0,
                    )
            except curses.error:
                pass
            return

        # Multi-line selection: determine top/bottom columns
        top_row = min(sr, er)
        bot_row = max(sr, er)

        if top_row == s.start_row:
            top_col = sc
            bot_col = ec
        else:
            top_col = ec
            bot_col = sc

        top_col = min(top_col, self._buffer.sizeof_line(top_row))
        bot_col = min(bot_col, self._buffer.sizeof_line(bot_row))

        # If this row is outside selected range, draw normally
        if relindex < top_row or relindex > bot_row:
            try:
                rendered = self._render_cached(buffer_line, width - 1, shift)
                ren.addnstr(index, 0, rendered, width, 0)
            except curses.error:
                pass
            return

        # Determine left/right selection bounds for this particular row
        if relindex == top_row:
            left = top_col
            right = self._buffer.sizeof_line(relindex)
        elif relindex == bot_row:
            left = 0
            right = bot_col
        else:
            left = 0
            right = self._buffer.sizeof_line(relindex)

        full = self._render_cached(buffer_line, width - 1, shift)
        vis_left = max(left, shift) - shift
        vis_right = min(right, shift + (width - 1)) - shift
        vis_left = max(0, min(vis_left, width - 1))
        vis_right = max(0, min(vis_right, width - 1))
        if vis_left >= vis_right:
            try:
                ren.addnstr(index, 0, full, width, 0)
            except curses.error:
                pass
            return

        try:
            if vis_left > 0:
                ren.addnstr(
                    index,
                    0,
                    full[:vis_left],
                    vis_left,
                    0,
                )
            ren.addnstr(
                index,
                vis_left,
                full[vis_left:vis_right],
                vis_right - vis_left,
                Basic.FNBUFFER_SELECTION.pair(),
            )
            if vis_right < (width - 1):
                ren.addnstr(
                    index,
                    vis_right,
                    full[vis_right:],
                    width - vis_right,
                    0,
                )
        except curses.error:
            pass

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
        command.use_screen(self._screen)
        command.use_editor(self._editor)
        self._mode.on_enter(self._editor)
        width = 64
        self._panels["debug"] = Panel(
            DEBUG_TEMPLATE.count("\n") + 2,
            width,
            0,
            self.width - width - 1,
            self._draw_debug,
        )
        self._debug.panel = self._panels["debug"]
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

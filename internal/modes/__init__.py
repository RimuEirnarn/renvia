"""Modes"""

# pylint: disable=unused-argument,import-outside-toplevel

import curses
from typing import Any, Callable

from internal import STATE, Basic
from internal.actions.delete import DeleteAction
from internal.editor import EditorState
from lymia import ReturnInfo, const
from lymia.colors import ColorPair
from lymia.data import ReturnType

MICE_HOVER = 268435456
MICE_SCROLL_UP = 65536
MICE_SCROLL_DOWN = 2097152

MICE_BIND = {
    curses.BUTTON1_CLICKED: "#1/CLICK",
    curses.BUTTON1_DOUBLE_CLICKED: "#1/DCLICK",
    curses.BUTTON1_PRESSED: "#1/PRESSED",
    curses.BUTTON1_RELEASED: "#1/RELEASED",
    curses.BUTTON1_TRIPLE_CLICKED: "#1/TCLICK",
    curses.BUTTON2_CLICKED: "#2/CLICK",
    curses.BUTTON2_DOUBLE_CLICKED: "#2/DCLICK",
    curses.BUTTON2_PRESSED: "#2/PRESSED",
    curses.BUTTON2_RELEASED: "#2/RELEASED",
    curses.BUTTON2_TRIPLE_CLICKED: "#2/TCLICK",
    curses.BUTTON3_CLICKED: "#3/CLICK",
    curses.BUTTON3_DOUBLE_CLICKED: "#3/DCLICK",
    curses.BUTTON3_PRESSED: "#3/PRESSED",
    curses.BUTTON3_RELEASED: "#3/RELEASED",
    curses.BUTTON3_TRIPLE_CLICKED: "#3/TCLICK",
    curses.BUTTON4_CLICKED: "#4/CLICK",
    curses.BUTTON4_DOUBLE_CLICKED: "#4/DCLICK",
    curses.BUTTON4_PRESSED: "#4/PRESSED",
    curses.BUTTON4_RELEASED: "#4/RELEASED",
    curses.BUTTON4_TRIPLE_CLICKED: "#4/TCLICK",
    MICE_SCROLL_DOWN: "SCROLL",
    MICE_HOVER: "HOVER",
}

TRIGGER_EVENT = (curses.KEY_LEFT, curses.KEY_RIGHT, curses.KEY_UP, curses.KEY_DOWN)


def _check_bufferline(editor: EditorState, nextline: int):
    ccol = editor.cursor.col
    sizeof = editor.buffer.sizeof_line(nextline)
    if ccol > sizeof:
        editor.cursor.col = sizeof
    editor.cursor.row = nextline


def go_up(editor: EditorState):
    """Go previous line"""
    if editor.cursor.row == 0:
        return ReturnType.CONTINUE
    _check_bufferline(editor, editor.cursor.row - 1)
    return ReturnType.CONTINUE


def go_down(editor: EditorState):
    """Go next line"""
    if editor.buffer.size == 0:
        return ReturnType.CONTINUE
    if editor.cursor.row == (editor.buffer.size - 1):
        return ReturnType.CONTINUE
    _check_bufferline(editor, editor.cursor.row + 1)
    return ReturnType.CONTINUE


def go_left(editor: EditorState):
    """Go previous char"""
    if editor.cursor.col == 0:
        return ReturnType.CONTINUE
    editor.cursor.col -= 1
    return ReturnType.CONTINUE


def go_right(editor: EditorState):
    """Go next char"""
    if editor.buffer.size == 0:
        return ReturnType.CONTINUE
    if editor.cursor.col == editor.buffer.sizeof_line(editor.cursor.row):
        return ReturnType.CONTINUE
    editor.cursor.col += 1
    return ReturnType.CONTINUE


def move_relmice(editor: EditorState):
    """Move relative to mice (mouse)"""
    dev_id, col, row, _, bstate = curses.getmouse()
    keybind = MICE_BIND.get(bstate, "UNKNOWN")
    editor.debug.status.set(f"Mouse#{dev_id} ({row}, {col}) [{bstate} -> {keybind}]")
    if bstate not in (
        curses.BUTTON1_RELEASED,
        curses.BUTTON1_CLICKED,
        MICE_SCROLL_UP,
        MICE_SCROLL_DOWN,
    ):
        return ReturnType.CONTINUE
    if row >= (editor.window.term_height - 2):
        return ReturnType.CONTINUE

    if STATE["use_naive_mice"] and bstate in (MICE_SCROLL_UP, MICE_SCROLL_DOWN):
        return go_up(editor) if bstate == MICE_SCROLL_UP else go_down(editor)
    if bstate in (MICE_SCROLL_UP, MICE_SCROLL_DOWN):  # Scroll up = B4
        return ReturnType.CONTINUE

    vrow = editor.window.start + row
    if vrow >= editor.buffer.size or editor.window.end <= 0:
        return ReturnType.CONTINUE
    sizeof = editor.buffer.sizeof_line(vrow)
    if col >= sizeof:
        col = sizeof - 1
    editor.cursor.move_to(vrow, col)
    return ReturnType.OK


def key_modifier(key: str, editor: EditorState):
    """Key modifier"""
    current_line = editor.cursor.row
    current_col = editor.cursor.col
    if key == "\n" and editor.buffer.size != 0:
        right = ""
        if editor.buffer.sizeof_line(current_line) > current_col:
            cline = editor.buffer[current_line]
            right = cline[current_col:]
            cline = cline.replace(right, "")
            editor.buffer[current_line] = cline
        editor.buffer.insert(current_line + 1, right)
        editor.cursor.row += 1
        editor.cursor.col = 0
        return ReturnType.OK

    if key == "\n" and editor.buffer.size == 0:
        editor.buffer.insert(0, "")
        editor.buffer.insert(1, "")
        editor.cursor.row += 1
        return ReturnType.OK

    if editor.buffer.size == 0:
        editor.buffer.insert(0, "")
    bufferline = editor.buffer[current_line]
    sizeof = len(bufferline)
    if current_col >= sizeof:
        editor.buffer.replace(current_line, bufferline + key)
        editor.cursor.col += 1
        return ReturnType.OK
    # insertion based on current column
    # abcdefghijk
    #    ^ (current column: insert r)
    # abcdrefghijk
    left = bufferline[:current_col]
    right = bufferline[current_col:]
    editor.cursor.col += 1
    editor.buffer.replace(current_line, left + key + right)
    return ReturnType.OK


def remove_current_char(editor: EditorState):
    """Remove current char from current buffer"""
    import internal.modes.normal

    if editor.buffer.size == 0:
        return ReturnType.ERR
    current_line = editor.cursor.row
    current_col = editor.cursor.col
    bufferline = editor.buffer[current_line]
    if bufferline == "":
        editor.buffer.delete(current_line)
        if editor.cursor.row == 0:
            return ReturnType.CONTINUE
        editor.cursor.row -= 1
        editor.cursor.col = editor.buffer.sizeof_line(editor.cursor.row)
        return ReturnType.OK
    if current_col >= len(bufferline):
        editor.buffer.replace(current_line, bufferline[:-1])
        editor.cursor.col -= 1
        return ReturnType.OK
    if current_col == 0 and not isinstance(
        editor.mode[0], internal.modes.normal.NormalMode
    ):
        if current_line == 0:
            return ReturnType.CONTINUE
        prev_line = editor.buffer[current_line - 1]
        editor.buffer[current_line - 1] = prev_line + bufferline
        editor.buffer.delete(current_line)
        editor.cursor.row -= 1
        return ReturnType.OK

    if isinstance(editor.mode[0], internal.modes.normal.NormalMode):
        left = bufferline[:current_col]
        right = bufferline[current_col + 1 :]
    else:
        left = bufferline[: current_col - 1]
        right = bufferline[current_col:]

    editor.buffer.replace(current_line, left + right)
    if editor.cursor.col == 0:
        return ReturnType.CONTINUE
    editor.cursor.col -= 1
    return ReturnType.OK

def rmc(editor: EditorState):
    """Remove current character"""
    import internal.modes.normal

    if editor.buffer.size == 0:
        return ReturnType.ERR
    current_line = editor.cursor.row
    current_col = editor.cursor.col
    bufferline = editor.buffer[current_line]

    if bufferline == "":
        editor.history.push(DeleteAction(editor.cursor.row, 0, '\n', 1))
        editor.buffer.delete(current_line)
        if editor.cursor.row == 0:
            return ReturnType.CONTINUE
        editor.cursor.row -= 1
        editor.cursor.col = editor.buffer.sizeof_line(editor.cursor.row)
        return ReturnType.OK
    if current_col >= len(bufferline):
        editor.history.push(DeleteAction(current_line, len(bufferline)-1, bufferline[-1]))
        editor.buffer.replace(current_line, bufferline[:-1])
        editor.cursor.col -= 1
        return ReturnType.OK
    if current_col == 0 and not isinstance(
        editor.mode[0], internal.modes.normal.NormalMode
    ):
        if current_line == 0:
            return ReturnType.CONTINUE
        prev_line = editor.buffer[current_line - 1]
        editor.buffer[current_line - 1] = prev_line + bufferline
        editor.history.push(DeleteAction(current_line, 0, "\n"))
        editor.buffer.delete(current_line)
        editor.cursor.row -= 1
        return ReturnType.OK

    if isinstance(editor.mode[0], internal.modes.normal.NormalMode):
        left = bufferline[:current_col]
        right = bufferline[current_col + 1 :]
    else:
        left = bufferline[: current_col - 1]
        right = bufferline[current_col:]

    editor.buffer.replace(current_line, left + right)
    editor.history.push(
        DeleteAction(editor.cursor.row, editor.cursor.col, bufferline[current_col])
    )
    if editor.cursor.col == 0:
        return ReturnType.CONTINUE
    editor.cursor.col -= 1
    return ReturnType.OK

CURSOR_KEYMAP = {
    curses.KEY_LEFT: go_left,
    curses.KEY_RIGHT: go_right,
    curses.KEY_UP: go_up,
    curses.KEY_DOWN: go_down,
    curses.KEY_MOUSE: move_relmice,
    const.KEY_ESC: lambda _: ReturnType.REVERT_OVERRIDE,
}


class Modes:
    """Modes"""

    theme: ColorPair
    term_vis: int = 1
    curs_style: int
    keymap: dict[int | str, Callable[[Any], ReturnType | ReturnInfo]] = {}

    def __init__(self) -> None:
        self._keymap: dict[int, Callable[[EditorState], ReturnType | ReturnInfo]] = {}
        self._record_delete: bool = False
        self._delete_hist = []
        for key, value in self.keymap.items():  # type: ignore
            if isinstance(key, str):
                key: int = ord(key)
            self._keymap[key] = value

    def record_backspace(
        self,
        key: int,
        editor: "EditorState",
        pre_callback: "Callable[[int, EditorState], None]",
    ):
        """Record backspace
        What it does: Is creating a separate History Node based on an action

        First, when a NAVIGATION key is detected, it calls pre_callback to alert
            parent Mode to push History of their current snapshot
        Then, this function will record cursor position and capture how many
            BACKSPACE received and capturing current line snapshot.

        Finally, when receiving a NAVIGATION key, the function push a Delete action."""
        if self._record_delete is False:
            pre_callback(key, editor)

    def handle_key(self, key: int, editor: EditorState) -> ReturnType | ReturnInfo:
        """Handle key"""
        for kfn, fn in self._keymap.items():
            if key == kfn:
                xfn = fn(editor)
                if xfn == ReturnType.REVERT_OVERRIDE:
                    return self.on_exit(editor)
                return xfn
        return ReturnType.CONTINUE

    def on_enter(self, editor: EditorState) -> ReturnType:
        """On enter event"""
        return NotImplemented

    def on_exit(self, editor: EditorState) -> ReturnType:
        """On exit event"""
        return NotImplemented

"""Visual mode"""

import curses
from functools import wraps
from typing import Callable

from lymia import ReturnInfo, ReturnType, const
from lymia.data import _StatusInfo
from internal.utils import set_cursor
from internal import Basic
from internal.editor import EditorState
import internal.modes.normal
from . import Modes, go_down, go_left, go_right, go_up, move_relmice

def to_normal(_: EditorState):
    """To normal mode"""
    return ReturnInfo(ReturnType.OVERRIDE, "context switching", internal.modes.normal.NormalMode())

def repatch(callback: Callable[[EditorState], ReturnType | ReturnInfo]):
    """Repatch"""

    @wraps(callback)
    def inner(editor: EditorState):
        ret = callback(editor)
        if ret != ReturnType.ERR or getattr(ret, "type", None) != ReturnType.ERR:
            editor.selection.end(editor.cursor.row, editor.cursor.col)
        return ret

    return inner


class VisualMode(Modes):
    """Visual mode"""

    theme = Basic.FNBUFFER_SELECT
    curs_style = 1

    keymap = {
        curses.KEY_UP: repatch(go_up),
        curses.KEY_DOWN: repatch(go_down),
        curses.KEY_LEFT: repatch(go_left),
        curses.KEY_RIGHT: repatch(go_right),
        curses.KEY_MOUSE: repatch(move_relmice),
        const.KEY_ESC: to_normal,
        'q': to_normal
    }

    def __init__(self) -> None:
        super().__init__()
        self._dbg: _StatusInfo | None = None

    def on_enter(self, editor: EditorState):
        curses.curs_set(self.term_vis)
        self._dbg = editor.debug.status
        set_cursor(self.curs_style)
        row = editor.cursor.row
        col = editor.cursor.col
        editor.selection.start(row, col)
        return ReturnType.OVERRIDE

    def on_exit(self, editor: EditorState):
        editor.selection.reset()
        return ReturnType.REVERT_OVERRIDE

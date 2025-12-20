"""Modes"""
# pylint: disable=unused-argument

import curses
from typing import Any, Callable

from internal import Basic
from internal.editor import EditorState
from lymia import ReturnInfo, const
from lymia.colors import ColorPair
from lymia.data import ReturnType

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

def key_modifier(key: str, editor: EditorState):
    """Key modifier"""
    current_line = editor.cursor.row
    current_col = editor.cursor.col
    if key == '\n' and editor.buffer.size != 0:
        right = ""
        if editor.buffer.sizeof_line(current_line) > current_col:
            cline = editor.buffer[current_line]
            right = cline[current_col:]
            cline = cline.replace(right, "")
            editor.buffer[current_line] = cline
        editor.buffer.insert(current_line+1, right)
        editor.cursor.row += 1
        editor.cursor.col = 0
        return ReturnType.OK

    if key == '\n' and editor.buffer.size == 0:
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
    if editor.buffer.size == 0:
        return ReturnType.ERR
    current_line = editor.cursor.row
    current_col = editor.cursor.col
    bufferline = editor.buffer[current_line]
    if bufferline == '':
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
    if current_col == 0:
        if current_line == 0:
            return ReturnType.CONTINUE
        prev_line = editor.buffer[current_line - 1]
        editor.buffer[current_line - 1] = prev_line + bufferline
        editor.buffer.delete(current_line)
        editor.cursor.row -= 1
        return ReturnType.OK
    left = bufferline[:current_col]
    right = bufferline[current_col+1:]
    editor.buffer.replace(current_line, left + right)
    if editor.cursor.col == 0:
        return ReturnType.CONTINUE
    editor.cursor.col -= 1
    return ReturnType.OK

CURSOR_KEYMAP = {
    curses.KEY_LEFT: go_left,
    curses.KEY_RIGHT: go_right,
    curses.KEY_UP: go_up,
    curses.KEY_DOWN: go_down,
    const.KEY_ESC: lambda _: ReturnType.REVERT_OVERRIDE
}

class Modes:
    """Modes"""
    theme: ColorPair
    term_vis: int = 1
    curs_style: int
    keymap: dict[int | str, Callable[[Any], ReturnType | ReturnInfo]] = {}

    def __init__(self) -> None:
        self._keymap: dict[int, Callable[[EditorState], ReturnType | ReturnInfo]] = {}
        for key, value in self.keymap.items(): # type: ignore
            if isinstance(key, str):
                key: int = ord(key)
            self._keymap[key] = value

    def handle_key(self, key: int, editor: EditorState) -> ReturnType | ReturnInfo:
        """Handle key"""
        for (kfn, fn) in self._keymap.items():
            if key == kfn:
                xfn = fn(editor)
                if xfn == ReturnType.REVERT_OVERRIDE:
                    return self.on_exit(editor)
                return xfn
        return ReturnType.CONTINUE

    def on_enter(self, editor: EditorState) -> ReturnType:
        return NotImplemented

    def on_exit(self, editor: EditorState) -> ReturnType:
        return NotImplemented

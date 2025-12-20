"""Normal Mode"""
import curses
from lymia import ReturnInfo, ReturnType
from lymia import const
from internal.editor import EditorState
from internal import Basic
from internal.utils import set_cursor
import internal.modes.edit
import internal.modes.helpmode
from . import Modes, CURSOR_KEYMAP, remove_current_char

def to_insert(_):
    """To insert mode"""
    return ReturnInfo(ReturnType.OVERRIDE, "context switching", internal.modes.edit.EditMode())

def to_help(_):
    """To help mode"""
    return ReturnInfo(ReturnType.OVERRIDE, "context switching", internal.modes.helpmode.HelpMode())

def go_right(editor: EditorState):
    """Go next char"""
    if editor.buffer.size == 0:
        return ReturnType.CONTINUE
    if editor.cursor.col >= (editor.buffer.sizeof_line(editor.cursor.row) - 1):
        return ReturnType.CONTINUE
    editor.cursor.col += 1
    return ReturnType.CONTINUE

def jump_to(editor: EditorState, col: int):
    """Jump to"""
    if editor.buffer.size == 0:
        return ReturnType.CONTINUE
    if col >= editor.buffer.sizeof_line(editor.cursor.row) or col == -1:
        editor.cursor.col = editor.buffer.sizeof_line(editor.cursor.row)
        return ReturnType.CONTINUE

    col = max(0, col)
    editor.cursor.col = col
    return ReturnType.CONTINUE

def undo(editor: EditorState):
    """Undo"""
    return editor.history.undo(editor)

def redo(editor: EditorState):
    """Redo"""
    return editor.history.redo(editor)

def write_to_disk(editor: EditorState):
    """Write to disk"""
    editor.buffer.write()
    editor.status.set("Saved")
    return ReturnType.OK

class NormalMode(Modes):
    """Modes"""
    curs_style = 1
    theme = Basic.FNBUFFER_NORMAL
    keymap = {
        **CURSOR_KEYMAP,
        curses.KEY_RIGHT: go_right,
        const.KEY_ESC: lambda _: ReturnType.CONTINUE,
        'i': to_insert,
        'a': to_insert,
        'q': lambda _: ReturnType.EXIT,
        'x': remove_current_char,
        '0': lambda editor: jump_to(editor, 0),
        '$': lambda editor: jump_to(editor, -1),
        'u': undo,
        "U": redo,
        'w': write_to_disk,
        'h': to_help
    }

    def on_enter(self, _: EditorState):
        curses.curs_set(self.term_vis)
        set_cursor(self.curs_style)
        return ReturnType.OVERRIDE

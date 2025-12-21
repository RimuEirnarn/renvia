"""Normal Mode"""
import curses
from lymia import ReturnInfo, ReturnType
from lymia import const
from internal.editor import EditorState
from internal import STATE, Basic, use_mice, disable_mice as mice_disable
from internal.utils import set_cursor
import internal.modes.edit
import internal.modes.helpmode
from . import Modes, CURSOR_KEYMAP, TRIGGER_EVENT, rmc

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
    return ReturnType.OK

def cjump_to(editor: EditorState, col: int):
    """Jump to (col)"""
    if editor.buffer.size == 0:
        return ReturnType.CONTINUE
    if col >= editor.buffer.sizeof_line(editor.cursor.row) or col == -1:
        editor.cursor.col = editor.buffer.sizeof_line(editor.cursor.row)
        return ReturnType.CONTINUE

    col = max(0, col)
    editor.cursor.col = col
    return ReturnType.OK

def rjump_to(editor: EditorState, row: int):
    """Jump to (row)"""
    if editor.buffer.size == 0:
        return ReturnType.CONTINUE
    if row >= editor.buffer.size or row == -1:
        row = editor.buffer.size - 1

    row = max(0, row)
    editor.cursor.row = row
    return ReturnType.OK

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

def mouse_toggle(_: EditorState):
    """Enable mice"""
    if STATE['use_mice']:
        mice_disable()
    else:
        use_mice()
    return ReturnType.OK

def toggle_mice_naivety(_: EditorState):
    """Toggle mice naivety"""
    STATE['use_naive_mice'] = not STATE['use_naive_mice']
    return ReturnType.OK

def tdebug(editor: EditorState):
    """Toggle debug"""
    editor.debug.show = False
    if not editor.debug.panel:
        return ReturnType.CONTINUE
    if editor.debug.panel.visible:
        editor.debug.panel.hide()
    else:
        editor.debug.panel.show()
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
        'x': rmc,
        '0': lambda editor: cjump_to(editor, 0),
        '$': lambda editor: cjump_to(editor, -1),
        'u': undo,
        "U": redo,
        'w': write_to_disk,
        'h': to_help,
        'g': lambda editor: rjump_to(editor, 0),
        'G': lambda editor: rjump_to(editor, -1),
        'l': mouse_toggle,
        ';': toggle_mice_naivety,
        '`': tdebug
    }

    def __init__(self) -> None:
        super().__init__()
        self._buffer = []
        self._during_undo: bool = False

    def handle_key(self, key: int, editor: EditorState) -> ReturnType | ReturnInfo:
        if key in TRIGGER_EVENT and self._during_undo:
            self._during_undo = False

        return super().handle_key(key, editor)

    def on_enter(self, _: EditorState):
        curses.curs_set(self.term_vis)
        set_cursor(self.curs_style)
        return ReturnType.OVERRIDE

"""Normal Mode"""

import curses
from string import printable
from lymia import ReturnInfo, ReturnType
from lymia import const
from internal.editor import EditorState
from internal import Basic
from internal.utils import set_cursor
import internal.modes.normal
from internal.actions.edit import EditAction
from . import Modes, CURSOR_KEYMAP, key_modifier, remove_current_char

mapped = tuple(map(ord, printable))


class EditMode(Modes):
    """Insert Modes"""

    curs_style = 5
    theme = Basic.FNBUFFER_EDIT
    keymap = {
        **CURSOR_KEYMAP,
        const.KEY_ESC: lambda _: ReturnInfo(
            ReturnType.OVERRIDE, "context switch", internal.modes.normal.NormalMode()
        ),
        curses.KEY_BACKSPACE: remove_current_char,
    }

    def __init__(self) -> None:
        super().__init__()
        self._buffer = []
        self._meta = {"col": 0, "row": 0, "buffer": self._buffer}

    def on_key(self, key: str, editor: EditorState):
        """On key event listener"""
        ret = key_modifier(key, editor)
        if ret == ReturnType.OK:
            self._buffer.append(key)
        return ret

    def on_enter(self, editor: EditorState):
        curses.curs_set(self.term_vis)
        set_cursor(self.curs_style)
        if editor.buffer.size == 0:
            pass
        elif editor.cursor.col == editor.buffer.sizeof_line(editor.cursor.row) - 1:
            editor.cursor.col += 1
        self._meta["col"] = editor.cursor.col
        self._meta["row"] = editor.cursor.row
        current_line = editor.buffer[editor.cursor.row]
        self._meta['cline'] = current_line
        return ReturnType.OVERRIDE

    def on_exit(self, editor: EditorState):
        if editor.buffer.size == 0:
            pass
        elif editor.cursor.col == 0:
            pass
        elif editor.cursor.col == editor.buffer.sizeof_line(editor.cursor.row):
            editor.cursor.col -= 1
        if self._buffer:
            editor.history.push(
                EditAction(
                    row=self._meta["row"],
                    col=self._meta["col"],
                    text="".join(self._meta["buffer"]),
                    # prev_line=self._meta['cline']
                )
            )
        return super().on_exit(editor)

    def handle_key(self, key: int, editor: EditorState) -> ReturnType | ReturnInfo:
        if key in mapped:
            return self.on_key(chr(key), editor)
        return super().handle_key(key, editor)

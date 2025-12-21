"""Normal Mode"""

import curses
from string import printable
from typing import Type
from lymia import ReturnInfo, ReturnType
from lymia import const
from internal.editor import EditorState
from internal import Basic
from internal.utils import set_cursor
import internal.modes.normal
from internal.actions.edit import EditAction
from internal.actions.delete import DeleteAction
from . import Modes, CURSOR_KEYMAP, TRIGGER_EVENT, key_modifier, remove_current_char

mapped = tuple(map(ord, printable))
BACKSPACE = (curses.KEY_BACKSPACE, const.KEY_BACKSPACE)

# COMPLETED: Make sure that in Edit Mode, BACKSPACE is properly recorded
# Known bugs:
# Enter Edit -> TYPE "Hello, " -> MOVE 1LU -> DELETE LINE -> MOVE 1LD -> TYPE "WORLD!" -> ESC
# On UNDO, only deletes "Hello, World!" but does not recover deleted line.


def current_line(editor: EditorState):
    """Current line"""
    return editor.buffer[editor.cursor.row]

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
        const.KEY_BACKSPACE: remove_current_char
    }

    def __init__(self) -> None:
        super().__init__()
        self._buffer = []
        self._meta = {"col": 0, "row": 0, "buffer": self._buffer}
        self._mode = "edit"

    def on_key(self, key: str, editor: EditorState):
        """On key event listener"""
        ret = key_modifier(key, editor)
        # editor.debug.status.set(f'{key} -> {self._buffer[:3]}')
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
        return ReturnType.OVERRIDE

    def _push(self, editor: EditorState, action: Type[EditAction | DeleteAction]):
        if self._buffer:
            editor.history.push(
                action(
                    row=self._meta['row'],
                    col=self._meta['col'],
                    text="".join(self._meta['buffer']) # type: ignore
                )
            )
            self._buffer.clear()
            self._meta = {
                'row': editor.cursor.row,
                "col": editor.cursor.col,
                "buffer": self._buffer
            }

    def on_exit(self, editor: EditorState):
        if editor.buffer.size == 0:
            pass
        elif editor.cursor.col == 0:
            pass
        elif editor.cursor.col == editor.buffer.sizeof_line(editor.cursor.row):
            editor.cursor.col -= 1
        if self._buffer and self._mode:
            self._push(editor, EditAction if self._mode == 'edit' else DeleteAction)
        return super().on_exit(editor)

    def handle_key(self, key: int, editor: EditorState) -> ReturnType | ReturnInfo:
        editor.debug.status.set(f"{key} | {self._mode} | {''.join(self._buffer)!r}")
        if key in TRIGGER_EVENT:
            self._push(editor, DeleteAction if self._mode == 'delete' else EditAction)
            self._meta = {
                'row': editor.cursor.row,
                "col": editor.cursor.col,
                "buffer": self._buffer
            }
            self._mode = ""
            return super().handle_key(key, editor)

        if key in BACKSPACE and self._mode == '':
            self._mode = 'delete'
        if key in mapped and self._mode == '':
            self._mode = 'edit'

        if key in BACKSPACE and self._mode == 'edit':
            self._push(editor, EditAction)
            char = current_line(editor)
            if len(char) == 0:
                char = '\n'
            elif editor.cursor.col >= len(char) - 1:
                char = char[-1]
            else:
                char = char[editor.cursor.col - 1]
            self._buffer.append(char)
            self._mode = 'delete'
            return super().handle_key(key, editor)
        if key in mapped and self._mode == 'delete':
            self._push(editor, DeleteAction)
            self._mode = 'edit'
            return self.on_key(chr(key), editor)

        if self._mode == 'delete' and key in BACKSPACE:
            char = current_line(editor)
            if len(char) == 0:
                char = '\n'
            elif editor.cursor.col >= len(char) - 1:
                char = char[-1]
            else:
                char = char[editor.cursor.col - 1]
            self._buffer.append(char)

        if key in mapped and self._mode == 'edit':
            return self.on_key(chr(key), editor)
        return super().handle_key(key, editor)

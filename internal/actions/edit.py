"""Insert action"""

from internal.editor import EditorState
from lymia import ReturnInfo, ReturnType
from . import Action

class EditAction(Action):
    """used for EditMode"""
    def __init__(self, row: int, col: int, text: str) -> None:
        self._row = row
        self._col = col
        self._text = text

    def execute(self, editor: EditorState) -> ReturnType | ReturnInfo:
        row = self._row
        col = self._col
        buffer_lines = self._text.splitlines()
        old = editor.buffer[row]
        if col == (len(old) - 1):
            prev = old[:col]
            current = buffer_lines[0]
            fcrow = prev + current
        else:
            prev_left = old[:col]
            prev_right = old[col:]
            current = buffer_lines[0]
            fcrow = prev_left + current
            editor.buffer[row] = fcrow
            if len(buffer_lines) == 1:
                editor.buffer[row] = fcrow + prev_right
            last = buffer_lines[-1] + prev_right
            lcur = len(buffer_lines[-1]) - 1
            editor.cursor.move_to(row + len(buffer_lines) - 1, lcur)
            buffer_lines[-1] = last
        for index, line in enumerate(buffer_lines[1:], 1):
            editor.buffer.insert(row + index, line)
        return ReturnType.OK

    def undo(self, editor: EditorState) -> ReturnType | ReturnInfo:
        row = self._row
        col = self._col
        prev_last = ""
        buffer_lines = self._text.splitlines()
        old = editor.buffer[row]
        prev = old[:col]
        last = buffer_lines[-1]
        prl = editor.buffer[row + buffer_lines.index(last)]
        if last != prl:
            prev_last = prl.replace(last, "")
        for index, line in enumerate(buffer_lines[1:], 1):
            if line != buffer_lines[index] and line != last: # type: ignore
                raise ValueError(f"Line {index} has mismarch data from actual buffer")
            editor.buffer.delete(row + 1)
        editor.buffer[row] = prev + prev_last
        editor.cursor.move_to(row, col)
        return ReturnType.OK

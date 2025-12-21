"""Delete"""

from internal.editor import EditorState
from lymia import ReturnInfo, ReturnType
from . import Action

class DeleteAction(Action):
    """used for EditMode"""
    def __init__(self, row: int, col: int, text: str, delcount: int = -1) -> None:
        self._row = row
        self._col = col
        self._text = text
        self._delcount = delcount if delcount >= 0 else len(text)

    def execute(self, editor: EditorState) -> ReturnType | ReturnInfo:
        row = self._row
        col = self._col
        text = self._text
        delcount = self._delcount

        if "\n" in text:
            bufferlines = text.splitlines()
            i0 = bufferlines[0]
            new = i0[:col - len(i0)]
            if i0 != editor.buffer[row]:
                return ReturnInfo(ReturnType.ERR, "i0 != current buffer", (i0, editor.buffer[row]))
            if new == '':
                editor.buffer.delete(row)
            else:
                editor.buffer[row] = new
            bufferlines.pop(0)
            for index, _ in enumerate(bufferlines, 1):
                editor.buffer.delete(row - index)
            return ReturnType.OK

        new = self._text[:col - delcount]
        if text == editor.buffer[row]:
            return ReturnInfo(ReturnType.ERR, "text == current buffer", (text, editor.buffer[row]))
        editor.buffer[row] = new
        return ReturnType.OK

    def undo(self, editor: EditorState) -> ReturnType | ReturnInfo:
        row = self._row
        col = self._col
        text = self._text
        delcount = self._delcount

        if "\n" in text:
            bufferlines = text.splitlines()
            n0row = row - (len(bufferlines) - 1)
            # i0 = bufferlines[-1]
            # editor.buffer.insert(n0row, i0[::-1])
            # bufferlines = bufferlines[:-1]
            for _, line in enumerate(bufferlines, 0):
                editor.buffer.insert(n0row, line[::-1])
            return ReturnType.CONTINUE

        if delcount != 1:
            delta = self._text[col - delcount:col]
        else:
            delta = self._text
        old = editor.buffer[row]
        if text[::-1] == old:
            return ReturnInfo(ReturnType.ERR, "text (reversed) == old", (text[::-1], old))
        # editor.buffer[row] = old + delta[::-1]
        left = old[:col]
        right = old[col:]
        editor.buffer[row] = left + delta[::-1] + right
        return ReturnType.OK

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
        # delcount = self._delcountdd

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

        old = editor.buffer[row]
        new = old[:(col + 1)]
        if text[::-1] == old:
            return ReturnInfo(ReturnType.ERR, "text == current buffer", (text, old))
        editor.buffer[row] = old.replace(new, "")
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

        # ???
        old = editor.buffer[row]
        if delcount != 1:
            delta = self._text[(col + 1) - delcount:(col + 1)]
        else:
            delta = self._text
            left = old[:col]
            right = old[col:]
            editor.buffer[row] = left + delta + right
            return ReturnType.OK
        if text[::-1] == old:
            return ReturnInfo(ReturnType.ERR, "text (reversed) == old", (text[::-1], old))
        # editor.buffer[row] = old + delta[::-1]
        # Kalau buffer:
        # Hello, World!
        #      ^ (0, 5)
        # <-- ',olleH'
        new = delta[::-1] + old
        editor.buffer[row] = new
        return ReturnType.OK

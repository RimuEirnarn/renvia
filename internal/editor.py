"""Editor"""

from dataclasses import dataclass
from typing import NamedTuple, TYPE_CHECKING

from lymia import Panel

from lymia.data import _StatusInfo as StatusInfo
from .buffer import Buffer
from .cursor import Cursor
from .history import HistoryTree

if TYPE_CHECKING:
    from internal.modes import Modes

def logical_xor(left: bool, right: bool):
    return left ^ right

@dataclass
class Selection:
    """Selection"""
    start_row: int
    start_col: int

    end_row: int
    end_col: int

    def __post_init__(self):
        self._active = False

    def __bool__(self):
        return self._active

    @property
    def going_left(self):
        """Selection is going left"""
        if not self._active:
            return False
        if self.start_row != self.end_row:
            return self.start_row > self.end_row
        return self.start_col > self.end_col

    @property
    def going_right(self):
        """Selection is going right"""
        if not self._active:
            return False
        if self.start_row != self.end_row:
            return self.end_row > self.start_row
        return self.end_col > self.start_col

    def slice(self, buffer: "Buffer") -> list[str]:
        """Slice some of the buffer like a butter!"""
        if not self._active:
            return []

        # Ensure rows are within buffer bounds
        buf_len = len(buffer)
        sr = max(0, min(self.start_row, buf_len - 1))
        er = max(0, min(self.end_row, buf_len - 1))
        sc = max(0, self.start_col)
        ec = max(0, self.end_col)

        # Same-line selection
        if sr == er:
            line = buffer[sr]
            line_len = buffer.sizeof_line(sr)
            left = min(sc, ec, line_len)
            right = min(max(sc, ec), line_len)
            return [line[left:right]]

        # Multi-line selection: produce lines from top->bottom
        top_row = min(sr, er)
        bot_row = max(sr, er)

        # Determine top and bottom column bounds based on which end is top
        if top_row == self.start_row:
            top_col = sc
            bot_col = ec
        else:
            top_col = ec
            bot_col = sc

        # Clamp cols to line lengths
        top_col = min(top_col, buffer.sizeof_line(top_row))
        bot_col = min(bot_col, buffer.sizeof_line(bot_row))

        out: list[str] = []

        # Top line: from top_col to end
        top_line = buffer[top_row]
        out.append(top_line[top_col:])

        # Middle full lines
        for row in range(top_row + 1, bot_row):
            out.append(buffer[row])

        # Bottom line: from start to bot_col
        bot_line = buffer[bot_row]
        out.append(bot_line[:bot_col])

        return out

    def start(self, row: int, col: int):
        """Mark start pos"""
        self._active = True
        self.start_row = row
        self.start_col = col

    def end(self, row: int, col: int):
        """Mark end pos"""
        self.end_row = row
        self.end_col = col

    def reset(self):
        """Reset state"""
        self._active = False
        self.start(0, 0)
        self.end(0, 0)

    def use(self):
        """Return START and END"""
        if not self._active:
            return
        return (self.start_row, self.start_col), (self.end_row, self.end_col)


@dataclass
class EditorView:
    """Editor view"""
    start: int
    end: int
    term_width: int
    term_height: int

@dataclass
class DebugState:
    """Debug State"""
    status: StatusInfo
    key: int
    cursor_row: int
    cursor_col: int
    cursor_style: int
    cursor_visibility: int
    term_width: int
    term_height: int
    buffer_size: int
    show: bool
    panel: Panel

class EditorState(NamedTuple):
    """Editor State"""
    cursor: Cursor
    buffer: Buffer
    history: HistoryTree
    status: StatusInfo
    window: EditorView
    debug: DebugState
    mode: list["Modes"]
    selection: Selection

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

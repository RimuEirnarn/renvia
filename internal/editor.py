"""Editor"""

from dataclasses import dataclass
from typing import NamedTuple

from lymia.data import _StatusInfo as StatusInfo
from .buffer import Buffer
from .cursor import Cursor
from .history import HistoryTree

@dataclass
class EditorView:
    """Editor view"""
    start: int
    end: int
    term_width: int
    term_height: int

class EditorState(NamedTuple):
    """Editor State"""
    cursor: Cursor
    buffer: Buffer
    history: HistoryTree
    status: StatusInfo
    window: EditorView

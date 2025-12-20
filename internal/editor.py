"""Editor"""

from typing import NamedTuple

from lymia.data import _StatusInfo as StatusInfo
from .buffer import Buffer
from .cursor import Cursor
from .history import HistoryTree

class EditorState(NamedTuple):
    """Editor State"""
    cursor: Cursor
    buffer: Buffer
    history: HistoryTree
    status: StatusInfo

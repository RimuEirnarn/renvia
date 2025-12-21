"""Actions"""
# pylint: disable=unused-argument

from typing import TYPE_CHECKING, Any
from lymia import ReturnInfo, ReturnType

if TYPE_CHECKING:
    from internal.editor import EditorState


class Action:
    """Action"""

    def execute(self, editor: "EditorState") -> ReturnType | ReturnInfo:
        """Execute this action"""
        return NotImplemented

    def undo(self, editor: "EditorState") -> ReturnType | ReturnInfo:
        """Undo this action"""
        return NotImplemented

    def __repr__(self) -> str:
        return f"<{type(self).__name__}>"

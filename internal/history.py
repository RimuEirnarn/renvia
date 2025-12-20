"""History structure, used for undo/redo tree"""

from typing import TYPE_CHECKING

from lymia import ReturnType
from internal.actions import Action

if TYPE_CHECKING:
    from internal.editor import EditorState

class HistoryNode:
    """History Node"""
    def __init__(self, act: Action | None, parent: "HistoryNode | None" = None, seq: int = 0) -> None:
        self.action = act
        self.parent: 'HistoryNode | None' = parent
        self.children: 'list[HistoryNode]' = []
        self.seq = seq

    def command(self):
        """Action command"""
        return NotImplemented

class HistoryTree:
    """History Tree"""
    def __init__(self) -> None:
        self.root: HistoryNode = HistoryNode(None)
        self.current: HistoryNode = self.root

    def push(self, act: Action):
        """Push an action to history tree"""
        node = HistoryNode(act, self.current)
        self.current.children.append(node)
        self.current = node

    def undo(self, editor: "EditorState"):
        """Undo an action"""
        if self.current is self.root:
            editor.status.set("Already at oldest change")
            return ReturnType.CONTINUE
        if self.current.action:
            ret = self.current.action.undo(editor)
            self.current = self.current.parent # type: ignore
            return ret
        return ReturnType.CONTINUE

    def redo(self, editor: "EditorState"):
        """Redo an action"""
        if not self.current.children:
            editor.status.set("Already at newest change")
            return ReturnType.CONTINUE
        node = self.current.children[-1]
        if node.action:
            rt = node.action.execute(editor)
            self.current = node
            return rt
        return ReturnType.CONTINUE

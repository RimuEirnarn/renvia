"""Help mode"""

import curses
from internal import Basic
from lymia import ReturnInfo, ReturnType
import internal.modes.normal
from internal.editor import EditorState
from internal.modes import Modes


class HelpMode(Modes):
    """Help mode"""
    curs_style = 0
    term_vis = 0
    theme = Basic.FNBUFFER_NORMAL
    keymap = {
        'q': lambda _: ReturnInfo(
            ReturnType.OVERRIDE, "context switch", internal.modes.normal.NormalMode()
        ),
    }

    def on_enter(self, editor: EditorState) -> ReturnType:
        curses.curs_set(self.term_vis)
        return ReturnType.OVERRIDE

    def on_exit(self, editor: EditorState) -> ReturnType:
        return ReturnType.REVERT_OVERRIDE

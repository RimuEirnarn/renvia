"""Internal"""
import curses
from lymia.colors import Coloring, ColorPair, color

class Basic(Coloring):
    """Color theme"""
    CURRENT_LINE = ColorPair(color.BLACK, color.YELLOW)
    FNBUFFER_NORMAL = ColorPair(color.BLACK, color.GREEN)
    FNBUFFER_EDIT = ColorPair(color.BLACK, color.YELLOW)
    FNBUFFER_SELECT = ColorPair(color.BLACK, color.BLUE)
    FNBUFFER_SELECTION = ColorPair(color.WHITE, color.BLACK)
    UNCOVERED = ColorPair(color.BLUE, -1)

STATE = {
    'use_naive_mice': True,
    "use_mice": False,
}

def use_mice():
    """Use mice"""
    STATE['use_mice'] = True
    # curses.mouseinterval(125)
    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
    print("\033[?1003h\n", flush=True) # allows capturing mouse movement

def disable_mice():
    """Disable mice"""
    STATE['use_mice'] = False
    curses.mousemask(-1)
    print("\033[?1002;1005l\n", flush=True)

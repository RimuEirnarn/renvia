from lymia.colors import Coloring, ColorPair, color

class Basic(Coloring):
    CURRENT_LINE = ColorPair(color.BLACK, color.YELLOW)
    FNBUFFER_NORMAL = ColorPair(color.BLACK, color.GREEN)
    FNBUFFER_EDIT = ColorPair(color.BLACK, color.YELLOW)
    FNBUFFER_SELECT = ColorPair(color.BLACK, color.BLUE)
    UNCOVERED = ColorPair(color.BLUE, -1)

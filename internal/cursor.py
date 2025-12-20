"""Cursor"""

from dataclasses import dataclass

@dataclass
class Cursor:
    """Cursor"""

    row: int
    col: int
    preferred_column: int # ???

    def move_left(self):
        """Move cursor to left"""
        if self.col == 0:
            return
        self.col -= 1

    def move_up(self):
        """Move cursor to up"""
        if self.row == 0:
            return
        self.row -= 1

    def move_to(self, row: int, col: int):
        self.row = row
        self.col = col

"""Buffer"""

import os.path


class Buffer:
    """Buffer zone"""

    def __init__(self, filename: str = "", buffer: list[str] | None = None) -> None:
        self._filename: str = filename
        self._buffer: list[str] = buffer or []
        self._dirty: bool = False
        if os.path.exists(filename):
            with open(filename, encoding='utf-8') as file:
                self._buffer = file.read().splitlines()

    def __getitem__(self, index: int):
        return self._buffer[index]

    def __setitem__(self, index: int, line: str):
        self._dirty = True
        self._buffer[index] = line

    @property
    def filename(self):
        """Buffer filename"""
        return self._filename

    @filename.setter
    def filename(self, filename: str):
        """Buffer filename"""
        self._filename = filename

    @property
    def buffer(self):
        """Buffer"""
        return tuple(self._buffer)

    @property
    def dirty(self):
        """Dirty flag"""
        return self._dirty

    def insert(self, pos: int, line: str):
        """Insert a text to a line"""
        self._dirty = True
        self._buffer.insert(pos, line)

    def replace(self, pos: int, line: str):
        """Replace a text from a line"""
        self[pos] = line

    def delete(self, pos: int):
        """Delete a line text"""
        self._dirty = True
        self._buffer.pop(pos)

    def write(self, encoding='utf-8'):
        """Write to disk"""
        if not self._dirty:
            return

        with open(self._filename, 'w', encoding=encoding) as file:
            file.write("\n".join(self._buffer))
        self._dirty = False

    def split_line(self, pos: int):
        """Split lines from a position"""
        return [pos]

    def __iter__(self):
        return iter(self._buffer)

    def __len__(self):
        return len(self._buffer)

    @property
    def size(self):
        """Buffer line sizes"""
        return len(self._buffer)

    def sizeof_line(self, index: int):
        """Size of a buffer line"""
        return len(self._buffer[index])

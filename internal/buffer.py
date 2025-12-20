"""Buffer"""

from os import stat

from lymia import ReturnInfo, ReturnType

BUFFER_MAX_SIZE = (1024 ** 2) * 1

class Buffer:
    """Buffer zone"""

    def __init__(self, filename: str = "", buffer: list[str] | None = None) -> None:
        self._filename: str = filename
        self._buffer: list[str] = buffer or []
        self._dirty: bool = False
        self.read()

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

    def read(self, encoding='utf-8'):
        """Read file"""
        try:
            st = stat(self._filename)
            if st.st_size >= BUFFER_MAX_SIZE:
                return ReturnInfo(ReturnType.ERR, "File is bigger than 1MB", "")
            with open(self._filename, encoding=encoding) as file:
                self._buffer = file.read().splitlines()
        except Exception as exc: # pylint: disable=broad-exception-caught
            return ReturnInfo(ReturnType.ERR, str(exc), type(exc).__name__)
        return ReturnType.OK

    def write(self, encoding='utf-8'):
        """Write to disk"""
        if not self._dirty:
            return ReturnType.CONTINUE

        if not self._filename:
            return ReturnInfo(ReturnType.ERR, "Filename is empty", "")

        try:
            with open(self._filename, 'w', encoding=encoding) as file:
                file.write("\n".join(self._buffer))
        except Exception as exc: # pylint: disable=broad-exception-caught
            return ReturnInfo(ReturnType.ERR, str(exc), type(exc).__name__)
        self._dirty = False
        return ReturnType.OK

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

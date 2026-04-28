from .base import Element, Col
from BlazeSudio.graphicsCore import Font
from typing import Iterable

__all__ = [
    "Text"
]

class Text(Element):
    __slots__ = ['font', 'txt', 'col']
    def __init__(self,
                 txt: str,
                 sze: int = 24,
                 col: Col.colourType = Col.Black,
                 fontOpts: Iterable[str] = None):
        """
        Just some text

        Args:
            txt: The text to display
            sze: The size of the text
            col: The colour of the text
            fontOpts: A list of font names or files to try and load, otherwise use default
        """
        if fontOpts is None:
            self.font = Font.Font(sze=sze)
        else:
            self.font = Font.SysFonts.pick(*fontOpts)
            self.font.size = sze
        self.txt = txt
        self.col = col
    @property
    def size(self):
        return self.font.size
    @size.setter
    def size(self, size: int):
        self.font.size = size
    def _op(self, mat, mxsze):
        return self._handleOp(self.font(self.txt, self.col), mat, mxsze)
    def _minsze(self, mat) -> tuple[float, float]:
        return self.font.linesize(self.txt)

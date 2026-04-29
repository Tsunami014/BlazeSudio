from .base import UIElement, IntEnum, Col
from BlazeSudio.graphicsCore import Font
from typing import Iterable

__all__ = [
    "Text"
]

class Text(UIElement):
    __slots__ = ['font', 'txt', 'col']
    """The Options (use | to combine)"""
    class O(IntEnum):
        """No options will be applied"""
        none = 0
        """Whether to break on words if go over the width (if not, breaks mid-word)"""
        BreakOnWord = 0b1
        """Centres the text (overrides RightAlign if both are applied)"""
        CentreAlign = 0b10
        """Aligns the text to the right"""
        RightAlign = 0b100

        """The defaults are: BreakOnWord"""
        Defaults = BreakOnWord
    def __init__(self,
                 txt: str,
                 sze: int = 24,
                 col: Col.colourType = Col.Black,
                 fontOpts: Iterable[str] = None,
                 *, opts: O = O.Defaults):
        """
        Just some text

        Args:
            txt: The text to display
            sze: The size of the text
            col: The colour of the text
            fontOpts: A list of font names or files to try and load, otherwise use default

        Keyword args:
            opts: The options to apply to the text
        """
        if fontOpts is None:
            self.font = Font.Font(sze=sze)
        else:
            self.font = Font.SysFonts.pick(*fontOpts)
            self.font.size = sze
        self.txt = txt
        self.col = col
        super().__init__(opts=opts)
    @property
    def size(self):
        return self.font.size
    @size.setter
    def size(self, size: int):
        self.font.size = size
    def _opInner(self, mxsze):
        return self.font(
                self.txt, self.col, mxsze[0],
                breakOnSpace=self.opts & self.O.BreakOnWord,
                align=0.5 if self.opts & self.O.CentreAlign else (1 if self.opts & self.O.RightAlign else 0))
    def _szes(self, mxsze, _):
        out = self.font.linesize_wid(self.txt, mxsze[0], breakOnSpace=self.opts & self.O.BreakOnWord)
        return self.font.linesize(self.txt[0]), out

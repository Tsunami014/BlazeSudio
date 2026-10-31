from .base import UIElement, BaseO, Col
from BlazeSudio.graphicsCore import Draw, Font
from typing import Iterable

__all__ = [
    "Elms"
]

class Text(UIElement):
    __slots__ = ['font', 'txt', 'col']
    class O(BaseO):
        _NXT = BaseO._NXT
        BreakOnWord = (_NXT := _NXT<<1)
        """Whether to break on words if go over the width (if not, breaks mid-word)"""

        Default = BreakOnWord
    def __init__(self,
                 txt: str,
                 sze: int = 24,
                 col: Col.colourType = Col.Black,
                 fontOpts: Iterable[str] = None,
                 *, opts: O = O.Default):
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
    def _opInner(self, mxsze, align=True):
        return self.font(
                self.txt, self.col, mxsze[0],
                breakOnSpace=self.opts & self.O.BreakOnWord,
                align=0.5 if self.opts & self.O.AlignCentre else (1 if self.opts & self.O.AlignRight else 0))
    def _szes(self, mxsze, _):
        if self.txt == "":
            return (0, 0), (0, 0)
        out = self.font.linesize_wid(self.txt, mxsze[0], breakOnSpace = self.opts & self.O.BreakOnWord)
        return self.font.linesize(self.txt[0]), out

class _LineBase(UIElement):
    __slots__ = ['col', 'thickness', 'round']
    def __init__(self, col, thick, round=0):
        """
        A line that stretches as far as it can in a direction and a certain thickness in another

        Args:
            col: The colour of the line
            thick: The thickness of the line
            round: The roundness of the line
        """
        self.col = col
        self.thickness = thick
        self.round = round
        super().__init__()
    def _opInner(self, mxsze):
        return Draw.Rect(0, 0, mxsze[0], mxsze[1], 0, self.col, roundness=self.round)

class Elms:
    Text = Text
    class HLine(_LineBase):
        __slots__ = []
        def _szes(self, mxsze, _):
            return (0, self.thickness), (mxsze[0], self.thickness)
    class VLine(_LineBase):
        __slots__ = []
        def _szes(self, mxsze, _):
            return (self.thickness, 0), (self.thickness, mxsze[1])

from .base import Element, Col
from BlazeSudio.graphicsCore import Font

__all__ = [
    "Text"
]

class Text(Element):
    __slots__ = ['font', 'txt', 'col']
    def __init__(self,
                 txt: str,
                 col: Col.colourType = Col.Black,
                 *fontOpts):
        """
        Just some text

        Args:
            txt: The text to display
            col: The colour of the text
        """
        self.font = Font.SysFonts.pick(*fontOpts)
        self.txt = txt
        self.col = col
    def _op(self, mat, mxsze):
        return self._handleOp(self.font(self.txt, self.col), mat, mxsze)
    def _minsze(self, mat) -> tuple[float, float]:
        return self.font.linesize(self.txt)

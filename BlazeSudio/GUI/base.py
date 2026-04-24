from BlazeSudio.graphicsCore.miscOps import Fill
from BlazeSudio.graphicsCore.stuff import Col, AvgClock
from BlazeSudio.graphicsCore.base import NormalisedOp, OpList, Vec2, Trans
from BlazeSudio.graphicsCore.core import Op, Core, _CoreCls
from BlazeSudio.graphicsCore import Ix
from typing import Self
import numpy as np

__all__ = ['UI', 'Element', 'BLANK']

BLANK = np.array([[]], np.uint8)

class _UITyping(_CoreCls):
    bgcol: Col.colourType
    clock: AvgClock
    def basicIx(self, maxfps: float|None = 120):
        """
        Handles basic interaction and clock ticking

        Basically just a wrapper for Ix.handleBasic and AvgClock.tick

        This can be used like `while UI.basicIx(): ...`

        Returns:
            bool: Whether the application should quit (False) or continue running (True)
        """

class _UIBase:
    def basicIx(self, maxfps: float = 120):
        self.clock.tick(maxfps)
        return Ix.handleBasic()
    def __call__(self, other: Op) -> Self:
        Core(Fill(self.bgcol)+other).rend()
    def __getattribute__(self, name):
        if name in ("bgcol", "clock", "__call__", "basicIx"):
            return super().__getattribute__(name)
        return Core.__getattribute__(name)

if 'UI' not in globals():
    UI: _UITyping = _UIBase()
    UI.bgcol = Col.White
    UI.clock = AvgClock()

class Element:
    __slots__ = []
    def _op(self, mat, crop) -> Op:
        return OpList()
    def __matmul__(self, oth) -> 'TransformedElm':
        return TransformedElm(self, oth)
    def __call__(self) -> NormalisedOp:
        sze = Core.size
        return self._op(Vec2(sze[0]/2, sze[1]/2).mat, (0, 0, sze[0], sze[1]))

class TransformedElm(Element):
    __slots__ = ['elm', 'oth']
    def __init__(self, elm, oth):
        self.elm: Element = elm
        self.oth: Trans = oth

    def _op(self, mat, crop):
        self.oth.apply(mat, BLANK, crop)
        return 

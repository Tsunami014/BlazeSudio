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
    def __call__(self, other: 'Element') -> Self: ...
    def Run(self, maxfps: float = None, *, quit_after: bool = True, fps_title: bool = False):
        """
        Handles the basic interaction loop, including clock ticking and rendering

        Basically just a wrapper for a lot of common stuff.

        Keyword args:
            quit_after: If True, after exiting will quit (speeds up window closing)
            fps_title: If True, every frame it will set the window title to the current average FPS. For debugging
        """

class _UIBase:
    __instance = None
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.bgcol = Col.White
            cls.__instance.clock = AvgClock()
            cls.elm = None
        return cls.__instance

    def __call__(self, other: 'Element') -> Self:
        if self.elm != other:
            self.elm = other
        return self
    def clear(self) -> Self:
        self.elm = None
        return self

    def Run(self, maxfps: float = None, *, quit_after: bool = True, fps_title: bool = False):
        while Ix.handleBasic():
            self.clock.tick(maxfps)
            if fps_title:
                Core.set_title(f'FPS: {round(self.clock.get_fps(), 2)}')
            if self.elm is None:
                Core(Fill(self.bgcol)).rend()
            else:
                Core(Fill(self.bgcol)+self.elm()).rend()
        if quit_after:
            Core.Quit()
    def __getattribute__(self, name):
        if name in (
                "__instance", "__new__",
                "elm", "bgcol", "clock",
                "__call__", "clear", "Run", "basicIx"):
            return super().__getattribute__(name)
        return Core.__getattribute__(name)

UI: _UITyping = _UIBase()

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

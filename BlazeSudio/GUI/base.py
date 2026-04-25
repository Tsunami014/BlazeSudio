from BlazeSudio.graphicsCore.miscOps import Fill, Crop
from BlazeSudio.graphicsCore.stuff import Col, AvgClock
from BlazeSudio.graphicsCore.base import Op, OpList, IDENTITY, Vec2, Trans
from BlazeSudio.graphicsCore.core import Core, _CoreCls
from BlazeSudio.graphicsCore._basey import Base
from BlazeSudio.graphicsCore import Ix, Trans as T
from typing import Self

__all__ = [
    'UI',
    'Element',
        'OpElm'
]


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
    def _op(self, mat, mxsze) -> Op:
        return OpList()
    def _minsze(self, mat) -> tuple[float, float]:
        return (0, 0)
    def __matmul__(self, oth) -> 'TransformedElm':
        return TransformedElm(self, oth)
    def __call__(self) -> Op:
        sze = Core.size
        return self._op(IDENTITY, (sze[0], sze[1]))


class TransformedElm(Element, Base):
    __slots__ = ['elm', 'oth']
    def __init__(self, elm, oth):
        self.elm: Element = elm
        self.oth: Trans = oth
    def _op(self, mat, mxsze):
        out = self.elm._op(mat, mxsze)
        rpos1 = getattr(out, "rpos", None)
        out @= self.oth
        rpos2 = getattr(out, "rpos", None)
        if rpos2 is not None:
            if rpos1 is not None:
                return out @ (rpos1-rpos2)
            return out @ -rpos2
        return out
    def _minsze(self, mat):
        out = self.elm._op(mat, (None, None)) @ self.oth
        rsze = out.rsze
        if rsze is not None:
            return rsze
        # Fallback to bounding rect
        crop = [0, 0, *self.elm._minsze(mat)]
        nmat, ncrop, _ = self.oth.apply(mat, crop, False)
        r = self._warpbbx(nmat, ncrop, [0,0,0,0])
        return r[2]-r[0], r[3]-r[1]

class OpElm(Element):
    __slots__ = ['op']
    def __init__(self, op: Op):
        self.op = op
    def _op(self, mat, mxsze):
        op = self.op if not hasattr(self.op, "getNormalisedPos") else self.op @ -self.op.getNormalisedPos(0, 0)
        if any(i is None for i in mxsze):
            if hasattr(op, "rsze") and any(i is not None for i in mxsze):
                rsze = op.rsze
                return (op @ Crop(0, 0,
                                    (mxsze[0] if mxsze[0] is not None else rsze[0]),
                                    (mxsze[1] if mxsze[1] is not None else rsze[1])
                            )) @ T.MatTrans(mat)
            return op @ T.MatTrans(mat)
        return (op @ Crop((0, 0), mxsze)) @ T.MatTrans(mat)
    def _minsze(self, mat):
        if hasattr(self.op, "rect"):
            r = self.op.rect()
            if r[0] is not None:
                return (r[2]-r[0], r[3]-r[1])
        return (0, 0)

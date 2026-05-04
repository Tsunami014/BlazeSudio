from BlazeSudio.graphicsCore.miscOps import Fill, Crop
from BlazeSudio.graphicsCore.stuff import Col, AvgClock
from BlazeSudio.graphicsCore.base import Op, OpList, IDENTITY, Trans
from BlazeSudio.graphicsCore.core import Core, _CoreCls
from BlazeSudio.graphicsCore._basey import Base
from BlazeSudio.graphicsCore import Ix, Events, Trans as T
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
    _mine = (
        "__instance", "__new__",
        "elm", "bgcol", "clock",
        "__call__", "clear", "Run", "basicIx",
    )
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
            mevs = []
            for ev in Ix.loopEvs():
                if Events.MouseEvent(ev):
                    mevs.append(ev)
                else:
                    self.elm.onevent(ev)
            # Create an event whose sole purpose is to signal the existance of the mouse
            mevs.append(Events.MouseEvent.create(
                timestamp = None,
                typ = Events.EvTyp.Mouse,
                window_id = None,
                pos = Ix.Mouse.pos,
            ))
            size = Core.size
            self.elm.mouseevents(mevs, (size[0], size[1]))
            if fps_title:
                Core.title = f'FPS: {round(self.clock.get_fps(), 2)}'
            if self.elm is None:
                Core(Fill(self.bgcol)).rend()
            else:
                Core(Fill(self.bgcol)+self.elm()).rend()
            self.clock.tick(maxfps)
        if quit_after:
            Core.Quit()
    def __getattribute__(self, name):
        if name == '_mine' or name in self._mine:
            return super().__getattribute__(name)
        return getattr(Core, name)
    def __setattr__(self, name, new):
        if hasattr(Core, name):
            return setattr(Core, name, new)
        return super().__setattr__(name, new)

UI: _UITyping = _UIBase()

class Element:
    __slots__ = []
    IMPORTANCE: int = 0
    """How important this element is (when judging element for event handling, higher = more important (handles events first))"""
    def _op(self, mat, mxsze) -> Op:
        return OpList()
    def _handleOp(self, op, mat, mxsze) -> Op:
        op2 = op if not hasattr(op, "getNormalisedPos") else op @ -op.getNormalisedPos(0, 0)
        return (op2 @ Crop((0, 0), mxsze)) @ T.MatTrans(mat)
    def _szes(self, mxsze, bound) -> tuple[tuple[float, float]|None, tuple[float, float]]|None:
        """
        Gets the sizes for the element. Returns a tuple of (minsize, maxsize)

        The mxsze is the largest the element can stretch, but if there is spacing try to only size it to bound.
        If this function returns None when bound is None, bound will actually be a value of interest; otherwise it will be the same as mxsze

        If minsze is None, it is (0, 0)
        """
        return None, (0, 0)
    def onevent(self, ev: Events.Event) -> bool:
        """Will not recieve mouse events. Returns whether it used the event (and so no other elements are allowed to use it)"""
        return True
    def mouseevents(self, evs: list[Events.MouseEvent], mxsze):
        pass
    def __matmul__(self, oth) -> 'TransformedElm':
        return TransformedElm(self, oth)
    def __call__(self) -> Op:
        sze = Core.size
        return self._op(IDENTITY, (sze[0], sze[1]))


class BaseO:
    def __getitem__(self, it) -> int:
        return {i: j for i, j in BaseO.__dict__.items() if not i.startswith('__')}[it]
    none = 0
    """No options will be applied"""
    Default = 0
    """The default options (None)"""
    CentreAlign = -0b1
    """Centres the element instead of having it align to the left (overrides RightAlign if both are applied)"""
    RightAlign = -0b10
    """Aligns to the right instead of the left"""

class UIElement(Element):
    __slots__ = ['opts']
    class O(BaseO): ...
    def __init__(self, *, opts: O = O.none):
        if opts is None:
            self.opts = self.O.none
        else:
            self.opts = opts
    def _opInner(self, mxsze) -> Op:
        return OpList()
    def _op(self, mat, mxsze) -> Op:
        return self._handleOp(self._opInner(mxsze), mat, mxsze)

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
    def _szes(self, mxsze, bound):
        out = []
        for sze in self.elm._szes(mxsze, bound):
            outercrop = [0,0,0,0]
            if sze is None:
                crop = outercrop
            else:
                crop = [0, 0, *sze]
            nmat, ncrop, _ = self.oth.apply(IDENTITY, crop, False)
            r = self._warpbbx(nmat, ncrop, outercrop)
            out.append((r[2]-r[0], r[3]-r[1]))
        return out

    def onevent(self, ev):
        return self.elm.onevent(ev)
    def mouseevents(self, evs, mxsze):
        # TODO: This (have to warp the event's positions and stuff)
        nevs = []
        return self.elm.mouseevents(nevs, self._szes(mxsze, mxsze)[1])

class OpElm(Element):
    __slots__ = ['op']
    def __init__(self, op: Op):
        self.op = op
    def _op(self, mat, mxsze):
        op = self.op if not hasattr(self.op, "getNormalisedPos") else self.op @ -self.op.getNormalisedPos(0, 0)
        return (op @ Crop((0, 0), mxsze)) @ T.MatTrans(mat)
    def _szes(self, mxsze, _):
        if hasattr(self.op, "rect"):
            r = self.op.rect()
            if r[0] is not None:
                out = (r[2]-r[0], r[3]-r[1])
                return out, out
        return None, mxsze

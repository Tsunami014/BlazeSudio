from BlazeSudio.graphicsCore.miscOps import Fill, Crop
from BlazeSudio.graphicsCore.stuff import Col, AvgClock
from BlazeSudio.graphicsCore.base import Op, OpList, IDENTITY, Trans
from BlazeSudio.graphicsCore.core import Core, _CoreCls
from BlazeSudio.graphicsCore._basey import Base
from BlazeSudio.graphicsCore import Ix, Events, Mouse, Trans as T
from typing import Self, Any

__all__ = [
    'UI',
    'Mouse',
    'Element',
        'OpElm'
]


class _UITyping(_CoreCls):
    bgcol: Col.colourType
    clock: AvgClock
    cursor: Any|bool
    def __call__(self, other: 'Element') -> Self: ...
    def Run(self, maxfps: float = None, *, quit_after: bool = True, fps_title: bool = False):
        """
        Handles the basic interaction loop, including clock ticking and rendering

        Basically just a wrapper for a lot of common stuff.

        Keyword args:
            quit_after: If True, after exiting will quit (speeds up window closing)
            fps_title: If True, every frame it will set the window title to the current average FPS. For debugging
        """
    def clearFocus(self):
        """Clears the focus from all elements"""

class _UIBase:
    __instance = None
    _mine = (
        "__instance", "__new__",
        "elm", "bgcol", "clock", "cursor",
        "__call__", "clear", "Run", "clearFocus",
    )
    def __new__(cls):
        if cls.__instance is None:
            inst = super().__new__(cls)
            cls.__instance = inst
            inst.bgcol = Col.Background
            inst.clock = AvgClock()
            inst.cursor = True

            cls.elm = None
        return cls.__instance

    def __call__(self, other: 'Element') -> Self:
        if self.elm != other:
            self.elm = other
        return self
    def clear(self) -> Self:
        self.elm = None
        return self

    def clearFocus(self):
        self.elm.clearFocus()

    def Run(self, maxfps: float = None, *, quit_after: bool = True, fps_title: bool = False):
        while Ix.handleBasic():
            self.cursor = True
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
            if self.cursor is True:
                Mouse.Default()
            elif not self.cursor:
                Mouse.Hide()
            else:
                Mouse.Set(self.cursor)
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


class BaseO:
    def __getitem__(self, it) -> int:
        return {i: j for i, j in BaseO.__dict__.items() if not i.startswith('__')}[it]
    none = 0
    """No options will be applied"""
    AlignCentre = (_NXT := 1)
    """Centres the element instead of having it align to the left (overrides AlignRight if both are applied)"""
    AlignRight = (_NXT := _NXT<<1)
    """Aligns to the right instead of the left"""
    PositionTop = (_NXT := _NXT<<1)
    """Positions the element at the top instead of the middle of layouts (overrides PositionBottom if both are applied)"""
    PositionBottom = (_NXT := _NXT<<1)
    """Positions the element at the bottom instead of the middle of layouts"""

    Default = 0

class _ElementBase: # MUST DEFINE __slots__ WITH ['opts']
    __slots__ = []
    IMPORTANCE: int = 0
    """How important this element is (when judging element for event handling, higher = more important (handles events first))"""
    class O(BaseO): ...
    def __init__(self, *, opts: BaseO = BaseO.Default):
        if opts is None:
            self.opts = self.O.Default
        else:
            self.opts = opts
    def _op(self, mat, mxsze) -> Op:
        return OpList()
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
        return False
    def mouseevents(self, evs: list[Events.MouseEvent], mxsze):
        pass
    def __matmul__(self, oth) -> 'TransformedElm':
        return TransformedElm(self, oth)
    def __call__(self) -> Op:
        sze = Core.size
        return self._op(IDENTITY, (sze[0], sze[1]))

    def clearFocus(self):
        pass

    def AlignL(self) -> Self:
        """Removes alignment flags.
        Alignment flags detail what alignment the content of this element is, not where it is positioned.
        Empty (default) is left."""
        self.opts = self.opts & ~(BaseO.AlignRight | BaseO.AlignCentre)
        return self
    def AlignC(self) -> Self:
        """Adds the CentreAlign flag.
        Alignment flags detail what alignment the content of this element is, not where it is positioned.
        Empty (default) is left."""
        self.opts = (self.opts | BaseO.AlignCentre) & ~BaseO.AlignRight
        return self
    def AlignR(self) -> Self:
        """Adds the RightAlign flag.
        Alignment flags detail what alignment the content of this element is, not where it is positioned."""
        self.opts = (self.opts | BaseO.AlignRight) & ~BaseO.AlignCentre
        return self
    def PositionT(self) -> Self:
        """Adds the PositionTop flag.
        Position flags change where the element is positioned in the parent layout perpendicular to its direction (e.g. top in a vertical layout is left and in a horizontal layout is the top)
        Empty (default) is centre."""
        self.opts = (self.opts | BaseO.PositionTop) & ~BaseO.PositionBottom
        return self
    def PositionM(self) -> Self:
        """Removes positioning flags.
        Position flags change where the element is positioned in the parent layout perpendicular to its direction (e.g. top in a vertical layout is left and in a horizontal layout is the top)
        Empty (default) is centre."""
        self.opts = self.opts & ~(BaseO.PositionBottom | BaseO.PositionTop)
        return self
    def PositionB(self) -> Self:
        """Adds the PositionBottom flag.
        Position flags change where the element is positioned in the parent layout perpendicular to its direction (e.g. top in a vertical layout is left and in a horizontal layout is the top)
        Empty (default) is centre."""
        self.opts = (self.opts | BaseO.PositionBottom) & ~BaseO.PositionTop
        return self

class Element(_ElementBase):
    __slots__ = ['opts']


class ElmWrapper(_ElementBase):
    def clearFocus(self):
        self.inner.clearFocus()
    def __getattribute__(self, name):
        if name[:5] == "Align":
            orig = super().__getattribute__(name)
            def ret():
                orig()
                getattr(self.inner, name)()
            return ret
        return super().__getattribute__(name)

class TransformedElm(ElmWrapper, Base):
    __slots__ = ['inner', 'opts', 'oth']
    def __init__(self, inner, oth, *, opts: BaseO = BaseO.Default):
        self.inner: Element = inner
        self.oth: Trans = oth
        ElmWrapper.__init__(self, opts=opts)
    def _op(self, mat, mxsze):
        out = self.inner._op(mat, mxsze)
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
        for sze in self.inner._szes(mxsze, bound):
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
        return self.inner.onevent(ev)
    def mouseevents(self, evs, mxsze):
        # TODO: This (have to warp the event's positions and stuff)
        nevs = []
        return self.inner.mouseevents(nevs, self._szes(mxsze, mxsze)[1])

class OpElm(Element):
    __slots__ = ['op']
    def __init__(self, op: Op, *, opts: BaseO = BaseO.Default):
        self.op = op
        super().__init__(opts=opts)
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

class UIElement(Element):
    def _opInner(self, mxsze) -> Op:
        return OpList()
    def _op(self, mat, mxsze) -> Op:
        op = self._opInner(mxsze)
        op2 = op if not hasattr(op, "getNormalisedPos") else op @ -op.getNormalisedPos(0, 0)
        return (op2 @ Crop((0, 0), mxsze)) @ T.MatTrans(mat)

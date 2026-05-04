from .base import Element, UIElement, BaseO, Col
from BlazeSudio.graphicsCore.base import Vec2
from BlazeSudio.graphicsCore import Draw, Trans, Events, Ix
from typing import Callable

__all__ = [
    "Button",
]

class ButtonBase(UIElement):
    __slots__ = ['inner', 'col', 'pad', 'round', 'onclick']
    class O(BaseO):
        FlexPad = 0b1
        """If enabled, the padding will be able to shrink to nothing if the layout is too small."""
    def __init__(self,
                 inner: Element,
                 col: Col.colourType = Col.Grey,
                 padding: float = 24,
                 roundness: float = 12,
                 onclick: Callable = None,
                 *, opts: O = O.Default):
        """
        A button to wrap an element in (e.g. text)

        Args:
            inner: The inner element to wrap
            col: The colour of the button
            padding: The padding from the inner element to the border
            roundness: The border radius of the button

        Keyword args:
            opts: The options to apply to the text
        """
        self.inner = inner
        self.col = col
        self.pad = padding
        self.round = roundness
        self.onclick = onclick
        super().__init__(opts=opts)
    def _op(self, mat, mxsze):
        return (Draw.Rect((0, 0), mxsze, 0, self.col, roundness=self.round) @ Trans.MatTrans(mat)) +\
                self.inner._op(mat @ Vec2(self.pad, self.pad).mat, (mxsze[0]-self.pad*2, mxsze[1]-self.pad*2))
    def _szes(self, mxsze, bound):
        out = self.inner._szes(mxsze, bound)
        if out is None:
            return None
        mn, mx = out
        if not self.opts & self.O.FlexPad:
            if mn is None:
                mn = (self.pad*2, self.pad*2)
            else:
                mn = (mn[0]+self.pad*2, mn[1]+self.pad*2)
        mx = (mx[0]+self.pad*2, mx[1]+self.pad*2)
        return mn, mx

    def onevent(self, ev):
        return self.inner.onevent(ev)
    def mouseevents(self, evs: list[Events.MouseEvent], mxsze):
        nevs = []
        for ev in evs:
            if self.onclick is not None and Events.MouseEvent(ev, Events.EvTyp.MouseUp):
                self.onclick(ev.pos)
            if ev.pos[0] >= self.pad and ev.pos[1] >= self.pad and ev.pos[0] <= mxsze[0]-self.pad*2 and ev.pos[1] <= mxsze[1]-self.pad*2:
                nevs.append(ev.translated(-self.pad, -self.pad))
        return self.inner.onmouseevent(nevs, (mxsze[0]-self.pad*2, mxsze[1]-self.pad*2))

class Button(ButtonBase):
    __slots__ = ['state']
    def __init__(self,
                 inner: Element,
                 col: Col.colourType = Col.Grey,
                 padding: float = 24,
                 roundness: float = 12,
                 onclick: Callable = None,
                 *, opts: ButtonBase.O = ButtonBase.O.Default):
        """
        A button to wrap an element in (e.g. text)

        Args:
            inner: The inner element to wrap
            col: The colour of the button
            padding: The padding from the inner element to the border
            roundness: The border radius of the button

        Keyword args:
            opts: The options to apply to the text
        """
        super().__init__(inner, col, padding, roundness, onclick, opts=opts)
        self.state = 0
    def _op(self, mat, mxsze):
        light = 0
        if self.state == 1: # Hovering
            light = 25
        elif self.state == 2: # Pressing
            light = -25
        return (Draw.Rect((0, 0), mxsze, 0, Col.lighten(self.col, light), roundness=self.round) @ Trans.MatTrans(mat)) +\
                self.inner._op(mat @ Vec2(self.pad, self.pad).mat, (mxsze[0]-self.pad*2, mxsze[1]-self.pad*2))

    def mouseevents(self, evs: list[Events.MouseEvent], mxsze):
        nevs = []
        for ev in evs:
            if self.onclick is not None and Events.MouseEvent(ev, Events.EvTyp.MouseUp):
                self.onclick(ev.pos)
            if ev.pos[0] >= self.pad and ev.pos[1] >= self.pad and ev.pos[0] <= mxsze[0]-self.pad*2 and ev.pos[1] <= mxsze[1]-self.pad*2:
                nevs.append(ev.translated(-self.pad, -self.pad))
        if evs:
            self.state = int(Ix.Mouse.left)+1
        else:
            self.state = 0
        return self.inner.mouseevents(nevs, (mxsze[0]-self.pad*2, mxsze[1]-self.pad*2))

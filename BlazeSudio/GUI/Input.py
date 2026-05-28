from .base import Element, UIElement, BaseO, Col
from .Elms import Text
from BlazeSudio.graphicsCore.base import Vec2
from BlazeSudio.graphicsCore import Draw, Trans, Events, Ix
from typing import Callable, Iterable

__all__ = [
    "Button",
    "Input",
]

class ButtonBase(UIElement):
    __slots__ = ['inner', 'col', 'pad', 'round', 'onclick']
    class O(BaseO):
        FlexPad = 0b1
        """If enabled, the padding will be able to shrink to nothing if the layout is too small."""
    def __init__(self,
                 inner: Element,
                 col: Col.colourType = Col.Primary,
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
            new = ev.translated(-self.pad, -self.pad)
            if ev.active:
                if self.onclick is not None and Events.MouseEvent(ev, Events.EvTyp.MouseUp):
                    self.onclick(ev.pos)
                if not (ev.pos[0] >= self.pad and ev.pos[1] >= self.pad and ev.pos[0] <= mxsze[0]-self.pad*2 and ev.pos[1] <= mxsze[1]-self.pad*2):
                    new.active = False
            nevs.append(new)
        return self.inner.onmouseevent(nevs, (mxsze[0]-self.pad*2, mxsze[1]-self.pad*2))

class Button(ButtonBase):
    __slots__ = ['state']
    def __init__(self,
                 inner: Element,
                 col: Col.colourType = Col.Primary,
                 padding: float = 24,
                 roundness: float = 12,
                 onclick: Callable = None,
                 *, opts: ButtonBase.O = ButtonBase.O.Default):
        """
        A button to wrap an element in (e.g. text)
        Changes colour and stuff too!

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
        found = False
        for ev in evs:
            new = ev.translated(-self.pad, -self.pad)
            if ev.active:
                found = True
                if self.onclick is not None and Events.MouseEvent(ev, Events.EvTyp.MouseUp):
                    self.onclick(ev.pos)
                if not (ev.pos[0] >= self.pad and ev.pos[1] >= self.pad and ev.pos[0] <= mxsze[0]-self.pad*2 and ev.pos[1] <= mxsze[1]-self.pad*2):
                    new.active = False
            nevs.append(new)
        if found:
            self.state = int(Ix.Mouse.left)+1
        else:
            self.state = 0
        return self.inner.mouseevents(nevs, (mxsze[0]-self.pad*2, mxsze[1]-self.pad*2))


class Input(Text):
    __slots__ = ['placehold', 'placeholdcol', 'active']
    def __init__(self,
                 txt: str = "",
                 sze: int = 24,
                 col: Col.colourType = Col.Black,
                 placeholder: str = "",
                 placeholdcol: Col.colourType = Col.Grey,
                 fontOpts: Iterable[str] = None,
                 *, opts: Text.O = Text.O.Default):
        """
        Text that you can edit! NOTE: This is not in a box, so it is not as intuative as InputBox for users. Consider using that instead.

        Args:
            txt: The initial text
            sze: The size of the text
            col: The colour of the text
            placeholder: The text to display when no text is inputted
            placeholdcol: The colour of the placeholder text
            fontOpts: A list of font names or files to try and load, otherwise use default

        Keyword args:
            opts: The options to apply to the text
        """
        self.placehold = placeholder
        self.placeholdcol = placeholdcol
        self.active = False
        super().__init__(txt, sze, col, fontOpts, opts=opts)
    @property
    def basecol(self):
        return Text.col.__get__(self, Input)
    @basecol.setter
    def basecol(self, new):
        Text.col.__set__(self, new)
    @property
    def col(self):
        if not super().txt:
            col = self.placeholdcol
        else:
            col = super().col
        return col if self.active else Col.lighten(col, 40)
    @col.setter
    def col(self, new):
        Text.col.__set__(self, new)

    @property
    def basetxt(self):
        return Text.txt.__get__(self, Input)
    @basetxt.setter
    def basetxt(self, new):
        Text.txt.__set__(self, new)
    @property
    def txt(self):
        rt = super().txt
        if not rt:
            return self.placehold
        return rt
    @txt.setter
    def txt(self, new):
        Text.txt.__set__(self, new)

    def onevent(self, ev: Events.Event) -> bool:
        if not self.active:
            return False
        if kev := Events.KeyEvent(ev, Events.EvTyp.KeyDown):
            if kev.key == "Backspace":
                self.basetxt = self.basetxt[:-1]
                return True
        elif tev := Events.TypingEvent(ev, Events.EvTyp.TypeEnd):
            self.basetxt += tev.text
            return True
        return False

    def mouseevents(self, evs: list[Events.MouseEvent], mxsze):
        clicks = [e for i in evs if (e:=Events.MouseEvent(i, Events.EvTyp.MouseUp))]
        if clicks:
            self.active = any(i.active for i in clicks)


class InputBox(Input):
    __slots__ = ['pad', 'border', 'round', 'bordercol']
    def __init__(self,
                 txt: str = "",
                 sze: int = 24,
                 col: Col.colourType = Col.Black,
                 pad: int = 8,
                 border: int = 5,
                 radius: int = 3,
                 placeholder: str = "",
                 placeholdcol: Col.colourType = Col.Grey,
                 bordercol: Col.colourType = Col.Purple,
                 fontOpts: Iterable[str] = None,
                 *, opts: Text.O = Text.O.Default):
        """
        Text in a box that you can edit!

        Args:
            txt: The initial text
            sze: The size of the text
            col: The colour of the text
            pad: The padding between the text and the border of the box
            border: The thickness of the border
            radius: The border radius of the box (0 to disable)
            placeholder: The text to display when no text is inputted
            placeholdcol: The colour of the placeholder text
            bordercol: The colour of the border
            fontOpts: A list of font names or files to try and load, otherwise use default

        Keyword args:
            opts: The options to apply to the text
        """
        self.pad = pad
        self.border = border
        self.round = radius
        self.bordercol = bordercol
        super().__init__(txt, sze, col, placeholder, placeholdcol, fontOpts, opts=opts)

    def _opInner(self, mxsze):
        hasborder = self.border > 0
        if (not hasborder) and self.pad <= 0:
            return super()._opInner(mxsze)
        xtra = self.pad+self.border
        innr = super()._opInner(mxsze) @ Vec2(0, xtra)
        if not hasborder:
            return innr
        r = innr.rect()
        col = self.bordercol if self.active else Col.lighten(self.bordercol, 40)
        return Draw.Rect((0,0), (r[2]+xtra*2, r[3]+xtra*2), self.border, col, roundness=self.round) + innr

    def _szes(self, mxsze, _):
        xtra = (self.pad + self.border) * 2
        return [(i[0]+xtra, i[1]+xtra) for i in super()._szes(mxsze, _)]

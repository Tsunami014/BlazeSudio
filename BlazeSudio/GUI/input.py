from .base import UI, Element, UIElement, ElmWrapper, BaseO, Col
from .elms import Text
from BlazeSudio.graphicsCore.base import Vec2
from BlazeSudio.graphicsCore import Mouse, Draw, Trans, Events, Ix
from typing import Callable, Iterable
import time

__all__ = [
    "Input"
]

class ButtonBase(UIElement, ElmWrapper):
    __slots__ = ['inner', 'col', 'pad', 'round', 'onclick']
    class O(BaseO):
        _NXT = BaseO._NXT
        FlexPad = (_NXT := _NXT<<1)
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
                UI.cursor = Mouse.HAND
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
        mt = Trans.MatTrans(mat)
        def mkRect(rad, l):
            return Draw.Rect((0, 0), mxsze, rad, Col.lighten(self.col, light+l), roundness=self.round) @ mt
        op = mkRect(0, 0)
        if round(self.pad) >= 8:
            op += mkRect(self.pad/3, -6) + mkRect(self.pad/8, -15)
        elif round(self.pad) >= 4:
            op += mkRect(self.pad/4, -12)
        elif round(self.pad) >= 2:
            op += mkRect(self.pad/2, -8)
        return op + self.inner._op(mat @ Vec2(self.pad, self.pad).mat, (mxsze[0]-self.pad*2, mxsze[1]-self.pad*2))

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
            UI.cursor = Mouse.HAND
            self.state = int(Ix.Mouse.left)+1
        else:
            self.state = 0
        return self.inner.mouseevents(nevs, (mxsze[0]-self.pad*2, mxsze[1]-self.pad*2))


class Input(Text):
    __slots__ = ['placehold', 'placeholdcol', 'active', 'cursor', 'onenter']
    class O(Text.O):
        _NXT = Text.O._NXT
        NoBlink = (_NXT := _NXT<<1)
        """Will prevent the cursor from blinking"""
        Multiline = (_NXT := _NXT<<1)
        """Will allow inputting multiple lines of text"""
        Terminal = (_NXT := _NXT<<1)
        """Will prefix the text with '>'"""
    def __init__(self,
                 txt: str = "",
                 sze: int = 24,
                 col: Col.colourType = Col.Black,
                 placeholder: str = "",
                 placeholdcol: Col.colourType = Col.Grey,
                 fontOpts: Iterable[str] = None,
                 onenter: Callable = None,
                 *, opts: O = O.Default):
        """
        Text that you can edit! NOTE: This is not in a box, so it is not as intuative as InputBox for users. Consider using that instead.

        Args:
            txt: The initial text
            sze: The size of the text
            col: The colour of the text
            placeholder: The text to display when no text is inputted
            placeholdcol: The colour of the placeholder text
            fontOpts: A list of font names or files to try and load, otherwise use default
            onenter: A function to call when enter is pressed ONLY if the input is NOT multiline. The first argument is the text in this input.

        Keyword args:
            opts: The options to apply to the text
        """
        self.cursor = 0
        self.placehold = placeholder
        self.placeholdcol = placeholdcol
        self.active = False
        self.onenter = onenter
        super().__init__(txt, sze, col, fontOpts, opts=opts)
    def clearFocus(self):
        self.active = False

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
        return Col.darken(col, 30) if self.active else col
    @col.setter
    def col(self, new):
        Text.col.__set__(self, new)

    @property
    def basetxt(self):
        """The text content inside the box"""
        return Text.txt.__get__(self, Input)
    @basetxt.setter
    def basetxt(self, new):
        Text.txt.__set__(self, new)
        self.cursor = max(0, min(self.cursor, len(new)))
    @property
    def txt(self):
        """The text as it's displayed (including cursor and placeholder text), to get text content of box use 'basetxt'"""
        rt = super().txt
        pref = '> ' if self.opts & self.O.Terminal else ''
        if not rt:
            if self.active:
                return pref+'|'
            return pref+self.placehold
        if self.active:
            if self.cursor >= len(rt):
                return pref+rt + '|'
            return pref+rt[:self.cursor] + \
                    ('|' if rt[self.cursor] == '\n' or (self.opts & self.O.NoBlink) or round(time.time()*2.5)%2 == 0 else ' ') + \
                    rt[self.cursor:]
        return rt
    @txt.setter
    def txt(self, new):
        self.basetxt = new

    def _move_vert(self, dy: int):
        if not (self.opts & self.O.Multiline):
            return

        lines = self.basetxt.split('\n')
        current_line_idx = self.basetxt.count('\n', 0, self.cursor)
        target_line_idx = current_line_idx + dy

        if 0 <= target_line_idx < len(lines):
            line_start = self.basetxt.rfind('\n', 0, self.cursor) + 1
            current_x = self.font.linewidth(self.basetxt[line_start:self.cursor])

            align = 0.5 if self.opts & self.O.AlignCentre else (1 if self.opts & self.O.AlignRight else 0)
            if align > 0:
                current_w = self.font.linewidth(lines[current_line_idx])
                target_w = self.font.linewidth(lines[target_line_idx])
                current_x += align * (target_w - current_w)

            target_line = lines[target_line_idx]
            target_line_start = sum(len(l) + 1 for l in lines[:target_line_idx])

            best_i = 0
            min_dist = float('inf')

            for i in range(len(target_line) + 1):
                dist = abs(current_x - self.font.linewidth(target_line[:i]))
                if dist < min_dist:
                    min_dist = dist
                    best_i = i

            self.cursor = target_line_start + best_i
        elif target_line_idx <= 0:
            self.cursor = 0
        else: # >= len(lines)
            self.cursor = len(self.basetxt)

    def onevent(self, ev: Events.Event) -> bool:
        if not self.active:
            return False
        if kev := Events.KeyEvent(ev, Events.EvTyp.KeyDown):
            if kev.key == "Escape":
                olda = self.active
                self.active = False
                return olda
            if kev.key == "Enter" or kev.key == "Return":
                if not self.opts & self.O.Multiline:
                    self.onenter(self.basetxt)
                    return True
                self.basetxt = self.basetxt[:self.cursor] + "\n" + self.basetxt[self.cursor:]
                self.cursor += 1
                return True
            if kev.key == "Backspace":
                ctrl = kev.modifs(ctrl=True)
                init = True
                while self.cursor > 0 and (init or (ctrl and self.basetxt[self.cursor-1] not in (' ', '\n', '\t'))):
                    if self.cursor < len(self.basetxt)-1:
                        self.basetxt = self.basetxt[:self.cursor-1] + self.basetxt[self.cursor:]
                        self.cursor -= 1
                    else:
                        self.basetxt = self.basetxt[:-1]
                        # By setting the text it auto caps the cursor
                    init = False
                return True
            elif kev.key == "Delete":
                ctrl = kev.modifs(ctrl=True)
                init = True
                while self.cursor < len(self.basetxt) and (init or (ctrl and self.basetxt[self.cursor] not in (' ', '\n', '\t'))):
                    self.basetxt = self.basetxt[:self.cursor] + self.basetxt[self.cursor+1:]
                    init = False
                return True
            elif kev.key == "Left":
                ctrl = kev.modifs(ctrl=True)
                init = True
                while self.cursor > 0 and (init or (ctrl and self.basetxt[self.cursor-1] not in (' ', '\n', '\t'))):
                    self.cursor -= 1
                    init = False
                return True
            elif kev.key == "Right":
                ctrl = kev.modifs(ctrl=True)
                init = True
                while self.cursor < len(self.basetxt) and (init or (ctrl and self.basetxt[self.cursor] not in (' ', '\n', '\t'))):
                    self.cursor += 1
                    init = False
                return True
            elif kev.key == "Up":
                self._move_vert(-1)
                return True
            elif kev.key == "Down":
                self._move_vert(1)
                return True
            elif kev.key == "Home":
                if self.opts & self.O.Multiline:
                    self.cursor = self.basetxt.rfind('\n', 0, self.cursor) + 1
                else:
                    self.cursor = 0
                return True
            elif kev.key == "End":
                if self.opts & self.O.Multiline:
                    next_n = self.basetxt.find('\n', self.cursor)
                    self.cursor = next_n if next_n != -1 else len(self.basetxt)
                else:
                    self.cursor = len(self.basetxt)
                return True
        elif tev := Events.TypingEvent(ev, Events.EvTyp.TypeEnd):
            txt = tev.text.replace('\n', '')
            self.basetxt = self.basetxt[:self.cursor] + txt + self.basetxt[self.cursor:]
            self.cursor += len(txt)
            return True
        return False

    def mouseevents(self, evs: list['Events.MouseEvent'], mxsze):
        if any(e.active for e in evs):
            UI.cursor = Mouse.TEXT
        clicks = [e for i in evs if (e := Events.MouseEvent(i, Events.EvTyp.MouseUp))]
        if clicks:
            self.active = any(i.active for i in clicks)

            if self.active:
                click = clicks[-1]
                align = 0.5 if self.opts & self.O.AlignCentre else (1 if self.opts & self.O.AlignRight else 0)

                if not self.basetxt:
                    self.cursor = 0
                else:
                    lines = self.basetxt.split('\n')
                    line_idx = max(0, min(int(click.pos[1] // max(1, self.font.lineheight)), len(lines) - 1))
                    target_line = lines[line_idx]

                    line_start = sum(len(l) + 1 for l in lines[:line_idx])
                    line_w = self.font.linewidth(target_line)
                    offset = max((mxsze[0] - line_w) * align, 0)

                    best_i = 0
                    min_dist = float('inf')

                    for i in range(len(target_line) + 1):
                        w = self.font.linewidth(target_line[:i])
                        dist = abs(click.pos[0] - w - offset)
                        if dist < min_dist:
                            min_dist = dist
                            best_i = i

                    self.cursor = line_start + best_i


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
                 onenter: Callable = None,
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
            onenter: A function to call when enter is pressed ONLY if the input is NOT multiline. The first argument is the text in this input.

        Keyword args:
            opts: The options to apply to the text
        """
        self.pad = pad
        self.border = border
        self.round = radius
        self.bordercol = bordercol
        super().__init__(txt, sze, col, placeholder, placeholdcol, fontOpts, onenter, opts=opts)

    def _opInner(self, mxsze):
        hasborder = self.border > 0
        if (not hasborder) and self.pad <= 0:
            return super()._opInner(mxsze)
        xtra = self.pad+self.border
        innr = super()._opInner([i-xtra*2 for i in mxsze]) @ Vec2(xtra, xtra)
        if not hasborder:
            return innr
        r = innr.rect()
        col = Col.darken(self.bordercol, 30) if self.active else self.bordercol
        return Draw.Rect((0,0), (r[2]+xtra*2, r[3]+xtra*2), self.border, col, roundness=self.round) + innr

    def _szes(self, mxsze, _):
        xtra = (self.pad + self.border) * 2
        return [(i[0]+xtra, i[1]+xtra) for i in super()._szes(mxsze, _)]

    def mouseevents(self, evs: list['Events.MouseEvent'], mxsze):
        xtra = self.pad + self.border
        super().mouseevents([e.translated(-xtra, -xtra) for e in evs], [i-xtra*2 for i in mxsze])


class Input:
    ButtonBase = ButtonBase
    Button = Button
    Input = Input
    InputBox = InputBox

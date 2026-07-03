from BlazeSudio.graphicsCore import Events, Col, Draw
from BlazeSudio.graphicsCore.base import OpList
from .base import UI, ElmWrapper, UIElement, Base, BaseO
from .input import InputBox
from .layouts import Lays
from typing import Iterable

class BG(UIElement):
    __slots__ = ['col', 'round']
    def __init__(self, col):
        self.col = col
        self.round = 0
        super().__init__()
    def _opInner(self, mxsze):
        return Draw.Rect(1, 1, mxsze[0]-2, mxsze[1]-2, 0, self.col, roundness=self.round-2)
    def _szes(self, mxsze, _):
        return None, mxsze

class Term(ElmWrapper, Base):
    __slots__ = ['inner', 'opts', 'box', '_bg', 'leader', 'cmds']
    def __init__(self,
                 leader: str = "/",
                 sze: int = 48,
                 pad: int = 16,
                 border: int = 10,
                 radius: int = 30,
                 bordercol: Col.colourType = Col.Grey,
                 bgcol: Col.colourType = Col.add_alpha(Col.LightGrey, -100),
                 fontOpts: Iterable[str] = None,
                 *, opts: BaseO = BaseO.Default):
        """
        A terminal that pops up on Alt+/ (configurable) for easy debugging!

        Args:
            sze: The size of the text
            pad: The padding between the text and the border of the box
            border: The thickness of the border
            radius: The border radius of the box (0 to disable)
            bordercol: The colour of the border
            bgcol: The colour of the background
            fontOpts: A list of font names or files to try and load, otherwise use default

        Keyword args:
            opts: The options to apply to this element.
        """
        self.leader = leader
        self.cmds = {}
        self._bg = BG(bgcol)
        self.box = InputBox(
            sze=sze, pad=pad, border=border, radius=radius, bordercol=bordercol, fontOpts=fontOpts,
            onenter=self.run, opts=InputBox.O.Default|InputBox.O.Terminal)
        self.inner = Lays.VBox[None, Lays.Stack[self._bg, self.box].PositionM()].add_stretch(10)
        ElmWrapper.__init__(self, opts=opts)

    def oncmd(self, cmd):
        """Use as a decorator on a function which takes an input of the command arguments (to get all use *args)"""
        def ret(fn):
            self.cmds[cmd] = self.cmds.get(cmd, [])+[fn]
            return fn
        return ret
    @property
    def onmessage(self):
        """Use as a decorator on a function which takes an input of the text (will not run when text is a command)"""
        return self.oncmd("")

    @property
    def bgcol(self) -> Col.colourType:
        return self._bg.col
    @bgcol.setter
    def bgcol(self, new):
        self._bg.col = new

    @property
    def active(self):
        return self.box.active
    @active.setter
    def active(self, new):
        self.box.active = new

    def clearFocus(self):
        self.box.active = False

    def run(self, cmd):
        self.box.active = False
        self.box.basetxt = ""
        if not cmd:
            return
        if cmd[0] == '/':
            name, *args = [i for i in cmd[1:].split(' ') if i]
            if (not name) or name not in self.cmds:
                return
            for fn in self.cmds[name]:
                fn(*args)
            return
        for fn in self.cmds.get("", []):
            fn(cmd)

    def _op(self, mat, mxsze):
        if not self.box.active:
            return OpList()
        self._bg.round = self.box.round
        return self.inner._op(mat, mxsze)
    def _szes(self, mxsze, bound):
        if not self.box.active:
            return (0, 0), (0, 0)
        return self.inner._szes(mxsze, bound)

    def onevent(self, ev: Events.Event) -> bool:
        if kev := Events.KeyEvent(ev, Events.EvTyp.KeyDown):
            if kev.key == self.leader and kev.modifs(alt=True):
                new = not self.box.active
                if new:
                    UI.clearFocus()
                self.box.active = new
                return True
        if self.box.active:
            return self.box.onevent(ev)
        return False

    def mouseevents(self, evs, mxsze):
        if not self.box.active:
            return
        self.inner.mouseevents(evs, mxsze)

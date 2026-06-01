from BlazeSudio.graphicsCore import Events, Col
from BlazeSudio.graphicsCore.base import OpList
from .base import ElmWrapper, Base, BaseO
from .input import InputBox
from .layouts import Lays
from typing import Iterable

class Term(ElmWrapper, Base):
    __slots__ = ['inner', 'box', 'opts', 'leader']
    def __init__(self,
                 leader: str = "/",
                 sze: int = 48,
                 pad: int = 16,
                 border: int = 10,
                 radius: int = 30,
                 bordercol: Col.colourType = Col.Grey,
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
            fontOpts: A list of font names or files to try and load, otherwise use default

        Keyword args:
            opts: The options to apply to this element.
        """
        self.leader = leader
        self.box = InputBox(
            sze=sze, pad=pad, border=border, radius=radius, bordercol=bordercol, fontOpts=fontOpts,
            onenter=self.run)
        self.inner = Lays.VBox[None, self.box].add_stretch(10)
        ElmWrapper.__init__(self, opts=opts)

    @property
    def active(self):
        return self.box.active
    @active.setter
    def active(self, new):
        self.box.active = new

    def run(self, cmd):
        self.box.active = False
        self.box.basetxt = ""
        print(cmd)

    def _op(self, mat, mxsze):
        if not self.box.active:
            return OpList()
        return self.inner._op(mat, mxsze)
    def _szes(self, mxsze, bound):
        if not self.box.active:
            return (0, 0), (0, 0)
        return self.inner._szes(mxsze, bound)

    def onevent(self, ev: Events.Event) -> bool:
        if kev := Events.KeyEvent(ev, Events.EvTyp.KeyDown):
            if kev.key == self.leader and kev.modifs(alt=True):
                self.box.active = not self.box.active
                return True
        if self.box.active:
            return self.box.onevent(ev)
        return False

    def mouseevents(self, evs, mxsze):
        if not self.box.active:
            return
        self.inner.mouseevents(evs, mxsze)

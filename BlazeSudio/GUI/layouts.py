from .base import Element, BaseO
from BlazeSudio.graphicsCore.base import OpList, Vec2
from dataclasses import dataclass
from typing import Self, Iterable

__all__ = ["Lays"]

class LayBase(Element):
    __slots__ = ['_children']
    class O(BaseO):
        Default = BaseO.Default | BaseO.PositionTop

    def __class_getitem__(cls, args):
        return cls(*args)

class StackLay(LayBase):
    def __init__(self, *children: tuple[Element], opts: LayBase.O = LayBase.O.Default):
        self._children: Iterable[Element] = list(children)
        super().__init__(opts=opts)

    def clearFocus(self):
        for c in self._children:
            c.clearFocus()

    def add_elm(self, oth: Element) -> Self:
        self._children.append(oth)
        return self
    def add_elms(self, oths: Iterable[Element]) -> Self:
        self._children.extend(oths)
        return self
    def insert_elm(self, idx: int, oth: Element) -> Self:
        self._children.insert(idx, oth)
        self._dirty = True
        return self
    def insert_elms(self, idx: int, oths: Iterable[Element]) -> Self:
        for i, oth in oths:
            self._children.insert(idx+i, oth)
            self._dirty = True
        return self

    def remove(self, oth: Element) -> bool:
        for idx, c in enumerate(self._children):
            if c[0] == oth:
                self._children.pop(idx)
                self._dirty = True
                return True
        return False
    def remove_many(self, oths: list[Element]) -> bool:
        for oth in oths:
            if not self.remove(oth):
                return False
        return True

    def __getitem__(self, idx) -> Element:
        return self._children[idx]
    def __setitem__(self, idx, new: Element):
        self._children[idx] = new
    def pop(self, idx) -> Element:
        return self._children.pop(idx)

    def _op(self, mat, mxsze):
        return sum((c._op(mat, mxsze) for c in self._children), OpList())

    def _szes(self, mxsze, bound):
        mn = (0, 0)
        mx = (0, 0)
        for c in self._children:
            s = c._szes(mxsze, bound)
            if s is None:
                return None
            m1 = s[0] or (0, 0)
            mn = tuple(min(m1[i], mn[i]) for i in range(2))
            mx = tuple(max(s[1][i], mn[i]) for i in range(2))
        return mn, mx

    def onevent(self, ev):
        for c in self._children:
            if c.onevent(ev):
                return True
        return False
    def mouseevents(self, evs, mxsze):
        for c in self._children:
            c.mouseevents(evs, mxsze)


@dataclass(eq=False, slots=True)
class ElementOut:
    element: Element|float|None
    isSpacing: bool
    stretch: float
    def __eq__(self, oth):
        if isinstance(oth, ElementOut):
            return self.element == oth.element
        return self.element == oth
    def __iter__(self):
        return iter((self.element, self.isSpacing, self.stretch))

class _BaseLayout(LayBase):
    __slots__ = ['_dirty', '_szesCache', 'spacing']
    _DIRECTION = None
    _FLIP = None
    def __init__(self, *children: tuple[Element], spacing: float = 10, opts: LayBase.O = LayBase.O.Default):
        """If a child is None, that will be stretch!"""
        self._children: list[tuple[Element|None|float, bool, float]] = []
        """[Element (or None for stretch or float for spacing), isSpacing, stretch]"""
        self._dirty = False
        self._szesCache = []
        if children:
            self.add_elms(children)
        self.spacing = spacing
        super().__init__(opts=opts)

    def clearFocus(self):
        for e, issp, _ in self._children:
            if (not issp) and e is not None:
                e.clearFocus()

    def add_elm(self, oth: Element, stretch: int = 1) -> Self:
        self._children.append((oth, False, stretch))
        self._dirty = True
        return self
    def add_elms(self, oths: Iterable[Element], stretches: int = 1) -> Self:
        self._children.extend([(i, False, stretches) for i in oths])
        self._dirty = True
        return self
    def add_spacing(self, size: float) -> Self:
        self._children.append((size, True, None))
        self._dirty = True
        return self
    def add_stretch(self, stretch: int = 1) -> Self:
        self._children.append((None, False, stretch))
        self._dirty = True
        return self
    def insert_elm(self, idx: int, oth: Element, stretch: int = 1) -> Self:
        self._children.insert(idx, (oth, False, stretch))
        self._dirty = True
        return self
    def insert_elms(self, idx: int, oths: Iterable[Element], stretches: int = 1) -> Self:
        for i, oth in oths:
            self._children.insert(idx+i, (oth, False, stretches))
            self._dirty = True
        return self
    def insert_spacing(self, idx: int, size: float) -> Self:
        self._children.insert(idx, (size, True, None))
        self._dirty = True
        return self
    def insert_stretch(self, idx: int, stretch: int = 1) -> Self:
        self._children.insert(idx, (None, False, stretch))
        self._dirty = True
        return self

    def remove(self, oth: Element) -> bool:
        for idx, c in enumerate(self._children):
            if c[0] == oth:
                self._children.pop(idx)
                self._dirty = True
                return True
        return False
    def remove_many(self, oths: list[Element]) -> bool:
        for oth in oths:
            if not self.remove(oth):
                return False
        return True

    def __getitem__(self, idx) -> ElementOut:
        it = self._children[idx]
        return ElementOut(it[0], it[1], it[2])
    def __setitem__(self, idx, new: ElementOut):
        self._children[idx] = tuple(new)
        self._dirty = True
    def pop(self, idx) -> ElementOut:
        self._dirty = True
        return self._children.pop(idx)


    def _getSzes(self, mxsze, bound):
        if not any(i[0] == (mxsze, bound) for i in self._szesCache) or self._dirty:
            # cursze, maxsze, stretch, elm, otheraxis
            szes = []

            # Build the list
            for c in self._children:
                if c[1]:
                    szes.append([0, c[0], 1, None, 0, 0])
                elif c[0] is None:
                    szes.append([0, None, c[2], None, 0, 0])
                else:
                    mn, mx = c[0]._szes(mxsze, bound)
                    szes.append([
                        (mn[self._DIRECTION] if mn is not None else 0), mx[self._DIRECTION],
                        c[2] or 1, c[0], 0, 0])
            # Find the lengths of all elements except stretch
            maxsize = mxsze[self._DIRECTION] - self.spacing*(len(szes)-1)
            while True:
                left = maxsize-sum(i[0] for i in szes)
                if left <= 0:
                    break
                n = sum(int(i[1] is None or i[0] < i[1])*(i[2] or 0) for i in szes if i[1] is not None)
                if n == 0:
                    break
                each = left / n
                for s in szes:
                    if s[1] is None or s[2] is None:
                        continue
                    s[0] = s[0] + each*s[2]
                    if s[1] is not None:
                        s[0] = min(s[0], s[1])

            # Find the depth of the elms, saving the ones that require a bound argument
            saves = []
            mxothsze = mxsze[1-self._DIRECTION]
            for s in szes:
                if s[3] is not None:
                    mxsz = (s[0], mxothsze)[::self._FLIP]
                    sz = s[3]._szes(mxsz, None)
                    if sz is None:
                        saves.append(s)
                    else:
                        s[4] = min(
                            sz[1][1-self._DIRECTION],
                            mxothsze)
            # Now depth the saved
            if saves:
                mxother = bound[1-self._DIRECTION]
                for s in saves:
                    mxsz = (s[0], mxothsze)[::self._FLIP]
                    bnd = (s[0], mxother)[::self._FLIP]
                    s[4] = min(
                        s[3]._szes(mxsz, bnd)[1][1-self._DIRECTION],
                        mxothsze)

            # Now calculate the other offsets
            mx = bound[1-self._DIRECTION]
            for s in szes:
                e = s[3]
                if e is not None:
                    s[5] = (0 if e.opts & BaseO.PositionTop else (1 if e.opts & BaseO.PositionBottom else 0.5)) * \
                        max(mx-s[4],0)

            # Now length the stretches
            n = sum(i[2] if i[1] is None else 0 for i in szes)
            if n != 0:
                maxsize = bound[self._DIRECTION] - sum(i[0] for i in szes) - self.spacing*(len(szes)-1)
                if maxsize > 0:
                    left = maxsize / n
                    for s in szes:
                        if s[1] is None:
                            s[0] = left*s[2]
            self._szesCache.append(((mxsze, bound), szes))
            self._szesCache = self._szesCache[-5:]
            return szes
        for match, szes in self._szesCache:
            if match == (mxsze, bound):
                return szes
        raise ValueError(
            "I don't know how you managed to achieve this"
        )

    def _op(self, mat, mxsze):
        li = OpList()
        offs = 0
        for s in self._getSzes(mxsze, mxsze):
            if s[3] is not None:
                v2 = Vec2((offs, s[5])[::self._FLIP])
                sz = (s[0], s[4])[::self._FLIP]
                li += s[3]._op(mat @ v2.mat, sz)
            offs += s[0] + self.spacing
        return li

    def _szes(self, mxsze, bound):
        if bound is None:
            return None
        szes = self._getSzes(mxsze, bound)
        minszes = [((e:=s[3]._szes(mxsze, bound)[0] or (0, 0))[self._DIRECTION], e[1-self._DIRECTION]) for s in szes if s[3] is not None]
        if len(minszes) == 0:
            minszes = [(0, 0)]
        space = self.spacing*(len(szes)-1)
        return (sum(s[0] for s in minszes)+space, max(s[1] for s in minszes))[::self._FLIP], \
            (sum(s[0] for s in szes)+space, max(s[4] for s in szes))[::self._FLIP]

    def onevent(self, ev):
        li = [i[0] for i in self._children if (not i[1]) and i[0] is not None]
        li.sort(key=lambda x: x.IMPORTANCE)
        for it in li:
            if it.onevent(ev):
                return True
        return False
    def mouseevents(self, evs, mxsze):
        offs = 0
        for s in self._getSzes(mxsze, mxsze):
            add = s[0]
            if s[3] is not None:
                nevs = []
                trns = (-offs, -s[5])[::self._FLIP]
                for ev in evs:
                    new = ev.translated(*trns)
                    if new.active and not (
                            offs <= ev.pos[self._DIRECTION] <= offs+add and
                            s[5] <= ev.pos[1-self._DIRECTION] <= s[5]+s[4]
                            ):
                        new.active = False
                    nevs.append(new)
                sz = (s[0], s[4])[::self._FLIP]
                s[3].mouseevents(nevs, sz)
            offs += add + self.spacing


class Lays:
    def __new__(cls, *_):
        raise NotImplementedError("This class cannot be instantiated!")

    class HBox(_BaseLayout):
        _DIRECTION = 0
        _FLIP = 1
    class VBox(_BaseLayout):
        _DIRECTION = 1
        _FLIP = -1

    @staticmethod
    def Offset(dx: float, dy: float, elm: Element):
        """Negative values will put the spacing on the right/bottom instead of left of the element"""
        if dy == 0:
            out = elm
        elif dy < 0:
            out = Lays.VBox(elm).add_spacing(-dy)
        else:
            out = Lays.VBox().add_spacing(dy).add_elm(elm)
        if dx == 0:
            return out
        if dx < 0:
            return Lays.HBox(out).add_spacing(-dx)
        return Lays.HBox().add_spacing(dx).add_elm(out)

    Stack = StackLay

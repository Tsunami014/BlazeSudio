from .base import Element
from BlazeSudio.graphicsCore.base import OpList, Vec2
from dataclasses import dataclass
from typing import Self, Iterable

__all__ = ["Layouts"]

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

class _BaseLayout(Element):
    __slots__ = ['_children', '_dirty', '_szesCache', 'spacing']
    _DIRECTION = None
    _FLIP = None
    def __init__(self, *children: tuple[Element], spacing: float = 10):
        """[Element (or None for stretch or float for spacing), isSpacing, stretch]"""
        self._children: list[tuple[Element|None|float, bool, float]] = []
        self._dirty = False
        self._szesCache = [None, None]
        if children:
            self.add_elms(children)
        self.spacing = spacing

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


    def _getSzes(self, mxsze):
        if self._szesCache[0] != mxsze or self._dirty:
            szes = []
            # cursze, maxsze, stretch, elm, otheraxis
            for c in self._children:
                if c[1]:
                    szes.append([0, c[0], 1, None, 0])
                elif c[0] is None:
                    szes.append([0, None, c[2], None, 0])
                else:
                    mn, mx = c[0]._szes(mxsze)
                    szes.append([mn[self._DIRECTION], mx[self._DIRECTION], c[2] or 1, c[0], mx[1-self._DIRECTION]])
            maxsize = mxsze[self._DIRECTION] - self.spacing*(len(szes)-1)
            while True:
                left = maxsize-sum(i[0] for i in szes)
                if left <= 0:
                    break
                n = sum(int(i[1] is None or i[0] < i[1])*(i[2] or 0) for i in szes)
                if n == 0:
                    break
                each = left / n
                for s in szes:
                    if s[2] is None:
                        continue
                    olds0 = s[0]
                    s[0] = olds0 + each*s[2]
                    if s[1] is not None:
                        s[0] = min(s[0], s[1])
                    if s[3] is not None and s[0] != olds0:
                        s[4] = min(
                            s[3]._szes((s[0], mxsze[1-self._DIRECTION])[::self._FLIP])[1][1-self._DIRECTION],
                            mxsze[1-self._DIRECTION])
            self._szesCache = [mxsze, szes]
            return szes
        return self._szesCache[1]

    def _op(self, mat, mxsze):
        li = OpList()
        offs = 0
        for s in self._getSzes(mxsze):
            if s[3] is not None:
                v2 = Vec2(offs, 0) if self._DIRECTION == 0 else Vec2(0, offs)
                li += s[3]._op(mat @ v2.mat, (s[0], mxsze[1-self._DIRECTION])[::self._FLIP])
            offs += s[0] + self.spacing
        return li

    def _szes(self, mxsze):
        szes = self._getSzes(mxsze)
        return (0, 0), (sum(s[0] for s in szes), max(s[4] for s in szes))[::self._FLIP]


class Layouts:
    def __new__(cls):
        raise NotImplementedError("This class cannot be instantiated!")

    class Horiz(_BaseLayout):
        _DIRECTION = 0
        _FLIP = 1
    class Vert(_BaseLayout):
        _DIRECTION = 1
        _FLIP = -1


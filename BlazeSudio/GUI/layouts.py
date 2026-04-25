from .base import Element
from BlazeSudio.graphicsCore.base import OpList, Vec2
from dataclasses import dataclass
from typing import Self, Iterable

__all__ = ["HLayout"]

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
    __slots__ = ['_children', 'spacing']
    def __init__(self, *children: tuple[Element], spacing: float = 10):
        """[Element (or None for stretch or float for spacing), isSpacing, stretch]"""
        self._children: list[tuple[Element|None|float, bool, float]] = []
        if children:
            self.add_elms(children)
        self.spacing = spacing

    def add_elm(self, oth: Element, stretch: int = None) -> Self:
        self._children.append((oth, False, stretch))
        return self
    def add_elms(self, oths: Iterable[Element], stretches: int = None) -> Self:
        self._children.extend([(i, False, stretches) for i in oths])
        return self
    def add_spacing(self, size: float) -> Self:
        self._children.append((size, True, None))
        return self
    def add_stretch(self, size: float) -> Self:
        self._children.append((None, False, size))
        return self
    def insert_elm(self, idx: int, oth: Element, stretch: int = None) -> Self:
        self._children.insert(idx, (oth, False, stretch))
        return self
    def insert_elms(self, idx: int, oths: Iterable[Element], stretches: int = None) -> Self:
        for i, oth in oths:
            self._children.insert(idx+i, (oth, False, stretches))
        return self
    def insert_spacing(self, idx: int, size: float) -> Self:
        self._children.insert(idx, (size, True, None))
        return self
    def insert_stretch(self, idx: int, size: float) -> Self:
        self._children.insert(idx, (None, False, size))
        return self

    def remove(self, oth: Element) -> bool:
        for idx, c in enumerate(self._children):
            if c[0] == oth:
                self._children.pop(idx)
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
    def pop(self, idx) -> ElementOut:
        return self._children.pop(idx)

    def _op(self, mat, mxsze):
        return OpList(*[i._op(mat, mxsze) for i in self._children if (not i[1]) and i[0] is not None])


class HLayout(_BaseLayout):
    def _op(self, mat, mxsze):
        minszes = {
            i[0]: i[0]._minsze(mat)[0] for i in self._children if (not i[1]) and i[0] is not None
        }
        spread = sum(i[2] for i in self._children if i[2] is not None)
        sze = sum(minszes[i[0]]+self.spacing for i in self._children if (not i[1]) and i[0] is not None) + \
                sum(i[0]+self.spacing for i in self._children if i[1]) - self.spacing
        each = max(mxsze[0]-sze, 0)/spread if spread != 0 else 0
        li = OpList()
        offs = 0
        for elm, isSpace, stretch in self._children:
            if isSpace:
                offs += elm + self.spacing
            else:
                if elm is not None:
                    sze = minszes[elm]
                    li += elm._op(mat @ Vec2(offs, 0).mat, (sze, mxsze[1]))
                    offs += sze + self.spacing
                offs += (0 if stretch is None else each)
        return li

    def _minsze(self, mat):
        szes = [i[0]._minsze(mat) for i in self._children if (not i[1]) and i[0] is not None]
        return sum(i[0]+self.spacing for i in szes)-self.spacing, max(i[1] for i in szes)

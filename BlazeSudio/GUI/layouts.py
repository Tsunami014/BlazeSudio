from .base import Element
from BlazeSudio.graphicsCore.base import NormalisedOp, OpList
from BlazeSudio.graphicsCore.Trans import Translate
from typing import Self

class _BaseLayout(Element):
    __slots__ = ['children', 'spacing']
    def __init__(self, children: list[Element|NormalisedOp] = None, spacing: float = 10):
        self.children: list[Element] = children or []
        self.spacing = spacing
    def __add__(self, oth: 'Element') -> Self:
        self.children.append(oth)
        return self
    def __sub__(self, oth: 'Element') -> Self:
        self.children.remove(oth)
        return self
    def _apply(self, comb, crop):
        return OpList([o[1] for o in comb if o is not None])
    def _op(self, mat, crop):
        ops = [i._op(mat, crop) for i in self.children]
        comb = [None, *((o.rect(), o) for o in ops), None]
        return self._apply(comb, crop)

# TODO: Stretch (do by making something that pretends to be an op and the layous just check for it)

class HLayout(_BaseLayout):
    def _apply(self, comb: list[list[NormalisedOp]], crop):
        wids = [i[0][2] for i in comb if i is not None]
        w = sum(wids) + (len(wids)-1)*self.spacing
        spacing = (crop[2]-crop[0])-w
        perspace = max(spacing, 0) / comb.count(None)
        li = OpList()
        offs = 0
        hspace = self.spacing / 2
        for c in comb:
            if c is None:
                offs += perspace
            else:
                r, op = c
                li += op @ Translate(offs+hspace, 0)
                offs += r[2] + self.spacing
        return li

from . import _basey
from typing import Self, overload
from abc import ABC, abstractmethod
from enum import IntEnum
import numpy as np

__all__ = [
    'Anchors',
    'IDENTITY',
    'OpFlags',
    'TransFlags',
    'Trans',
        'Vec2',
        'MatTrans',
    'Op',
        'NormalisedOp',
        'OpList',
        'TransOp'
]

class Anchors:
    _nx = 'normalise_x'
    _ny = 'normalise_y'
    TopLeft =  {_nx: 0,   _ny: 0}
    TopMid =   {_nx: 0.5, _ny: 0}
    TopRight = {_nx: 1,   _ny: 0}
    MidLeft =  {_nx: 0,   _ny: 0.5}
    Middle =   {_nx: 0.5, _ny: 0.5}
    MidMid =   Middle
    MidRight = {_nx: 1,   _ny: 0.5}
    BotLeft =  {_nx: 0,   _ny: 1}
    BotMid =   {_nx: 0.5, _ny: 1}
    BotRight = {_nx: 1,   _ny: 1}

IDENTITY = np.array([
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1]
], float)

class OpFlags(IntEnum):
    """
    Flags that make Operations act differently.
    Only for manual use if you know what you're doing.
    """
    NoFlags = 0
    """Has no flags. Is not special"""
    List = 0b1
    """Is an OpList"""
    Trans = 0b10
    """Is a TransOp"""
    Normalised = 0b100
    """Is a NormalisedOp"""
    Reset = 0b1000
    """Is a reset op. Every op before it will be ignored"""

class TransFlags(IntEnum):
    NoFlags = 0
    """Has no flags. Is not special"""
    Group = 0b1
    """Is a TransGroup"""
    Matrix = 0b10
    """Is a matrix transformation"""


class Trans(ABC):
    __slots__ = []
    flags = TransFlags.NoFlags

    @abstractmethod
    def apply(self, mat: np.ndarray, crop: tuple, defSmth: bool) -> tuple[np.ndarray, tuple, bool]: ...

    def __pos__(self) -> Self: return self
    def __add__(self, oth) -> 'Trans':
        if not isinstance(oth, Trans):
            oth = Vec2(*oth)
        if self.flags & TransFlags.Group:
            if oth.flags & TransFlags.Group:
                return TransGroup(*self.membs, *oth.membs)
            return TransGroup(*self.membs, oth)
        if oth.flags & TransFlags.Group:
            return TransGroup(self, *oth.membs)
        if self.flags & TransFlags.Matrix and oth.flags & TransFlags.Matrix:
            return MatTrans(oth.mat @ self.mat)
        return TransGroup(self, oth)

    def __iter__(self):
        return iter((self,))
    def flatten(self):
        return [self]

class MatTrans(Trans, _basey.Base):
    __slots__ = ['mat']
    flags = TransFlags.Matrix

    def __init__(self, mat):
        self.mat = np.array(mat, float)

    def apply(self, mat: np.ndarray, crop, defSmth: bool):
        return mat @ self.mat, crop, defSmth

class Vec2(MatTrans):
    __slots__ = ['pos']

    @property
    def mat(self) -> np.ndarray:
        return np.array([
            [1, 0, self.pos[0]],
            [0, 1, self.pos[1]],
            [0, 0, 1]
        ], float)

    @overload
    def __init__(self, x: float, y: float): ...
    @overload
    def __init__(self, pos): ...
    def __init__(self, *args):
        match len(args):
            case 1:
                self.pos = args[0]
            case 2:
                self.pos = args
            case _:
                raise TypeError(
                    f'Expected 1 or 2 arguments, found {len(args)}!'
                )

    @property
    def x(self) -> float:
        return self.pos[0]
    @property
    def y(self) -> float:
        return self.pos[1]

    def __iter__(self):
        return iter(self.pos)
    def __len__(self):
        return 2
    def __getitem__(self, it):
        return self.pos[it]

    def __neg__(self):
        return Vec2(-self.pos[0], -self.pos[1])
    def __abs__(self):
        return Vec2(abs(self.pos[0]), abs(self.pos[1]))

    def __add__(self, oth):
        if isinstance(oth, Trans):
            return super().__add__(oth)
        if not hasattr(oth, '__len__'):
            return Vec2(self.pos[0] + oth, self.pos[1] + oth)
        return Vec2(self.pos[0] + oth[0], self.pos[1] + oth[1])
    def __sub__(self, oth):
        if not hasattr(oth, '__len__'):
            return Vec2(self.pos[0] - oth, self.pos[1] - oth)
        return Vec2(self.pos[0] - oth[0], self.pos[1] - oth[1])
    def __mul__(self, oth):
        if not hasattr(oth, '__len__'):
            return Vec2(self.pos[0] * oth, self.pos[1] * oth)
        return Vec2(self.pos[0] * oth[0], self.pos[1] * oth[1])
    def __floordiv__(self, oth):
        if not hasattr(oth, '__len__'):
            return Vec2(self.pos[0] // oth, self.pos[1] // oth)
        return Vec2(self.pos[0] // oth[0], self.pos[1] // oth[1])
    def __div__(self, oth):
        if not hasattr(oth, '__len__'):
            return Vec2(self.pos[0] / oth, self.pos[1] / oth)
        return Vec2(self.pos[0] / oth[0], self.pos[1] / oth[1])

class TransGroup(Trans):
    __slots__ = ['membs', '_fixed']
    flags = TransFlags.Group
    def __init__(self, *transs):
        self.membs = list(transs)
        self._fixed = False

    def _unpack(self, li):
        for it in li:
            if it.flags & TransFlags.Group:
                yield from self._unpack(it)
            else:
                yield it

    def fix(self):
        if self._fixed:
            return
        it = self._unpack(self.membs)
        membs = []
        m = next(it, None)
        while m is not None:
            m2 = m
            while (nxt := next(it, None)) is not None and \
                    m.flags & nxt.flags & TransFlags.Matrix:
                m2 = MatTrans(nxt.mat @ m2.mat)
                m = nxt
            membs.append(m2)
            m = nxt
        self.membs = membs
        self._fixed = True

    def apply(self, *args):
        if not self._fixed:
            self.fix()
        for m in self.membs[::-1]:
            args = m.apply(*args)
            if args is None:
                return None
        return args

    def __iter__(self):
        if not self._fixed:
            self.fix()
        return iter(self.membs)
    def flatten(self):
        if not self._fixed:
            self.fix()
        return self.membs


class Op(ABC, _basey.Base):
    __slots__ = ['flags']

    @abstractmethod
    def apply(self, mat: np.ndarray, arr: np.ndarray, crop, defSmth: bool) -> np.ndarray: ...

    def frozen(self) -> Self:
        """Get the frozen verson of this operation"""
        return self
    def freeze(self) -> Self:
        """Freezes this operation and returns it"""
        return self

    def __pos__(self) -> Self: return self
    def __add__(self, oth) -> 'OpList':
        if oth.flags & OpFlags.List:
            return OpList(self, *oth.ops)
        return OpList(self, oth)

    def __matmul__(self, oth) -> 'TransOp':
        if oth is None:
            return TransOp(self.frozen())
        if not isinstance(oth, Trans):
            oth = Vec2(*oth)
        return TransOp(self.frozen(), oth)

    def _op(self, mat, crop) -> Self: # For GUI integration
        return self

    def __iter__(self):
        return iter((self,))
    def flatten(self):
        return [self]

class NormalisedBase:
    def rect(self):
        """Returns a tuple in the format (topleft_x, topleft_y, width, height)"""
        return None, None, None, None
    @property
    def rpos(self):
        """Get the position as of self.rect"""
        p = self.rect()[:2]
        if p[0] is None:
            return None
        return Vec2(p)
    @property
    def rsze(self):
        """Get the size as of self.rect"""
        s = self.rect()[2:]
        if s[0] is None:
            return None
        return Vec2(s)
    def getNormalisedPos(self, normalise_x: float = 0, normalise_y: float = 0):
        """Get the true position of a normalised point."""
        x, y, wid, hei = self.rect()
        if x is None:
            return None, None
        return Vec2(x + wid * normalise_x, y + hei * normalise_y)

class NormalisedOp(Op, NormalisedBase):
    def __init__(self, *, normalise_x = None, normalise_y = None):
        self.flags = OpFlags.Normalised
        if normalise_x is not None and normalise_y is not None:
            ox, oy = self.getNormalisedPos(normalise_x, normalise_y)
            if normalise_x is None:
                ox = 0
            if normalise_y is None:
                oy = 0
            self._translate(-ox, -oy)

    @abstractmethod
    def _translate(self, x, y): ...

class OpList(Op, NormalisedBase):
    __slots__ = ['ops', '_fixed', 'flags']
    def __init__(self, *ops):
        self.ops = ops
        self._fixed = False
        self.flags = OpFlags.List

    def rect(self):
        """
        Get the rect (x, y, width, height) that surrounds all ops in this list.

        If any operation is not a NormalisedOp, will return (None, None, None, None)
        """
        if not self._fixed:
            self.fix()
        if not self.flags & OpFlags.Normalised:
            return None, None, None, None
        rs = [
            (x, y, x+w, y+h) for x, y, w, h in
                (o.rect() for o in self.ops)
        ]
        topLeft = [
            min(i[0] for i in rs),
            min(i[1] for i in rs),
        ]
        botRight = [
            max(i[2] for i in rs),
            max(i[3] for i in rs),
        ]
        return *topLeft, botRight[0]-topLeft[0], botRight[1]-topLeft[1]

    def _unpack(self, li):
        for it in li:
            if it.flags & OpFlags.List:
                yield from self._unpack(it)
            else:
                yield it

    def fix(self):
        if self._fixed:
            return
        ops = list(self._unpack(self.ops))
        self.flags &= ~OpFlags.Reset # Remove the reset flag
        for idx, o in enumerate(ops[::-1]):
            if o.flags & OpFlags.Reset:
                self.ops = ops[-1-idx:]
                self.flags |= OpFlags.Reset # Add the reset flag
                break # We're going backwards
        else:
            self.ops = ops
        if all(i.flags & OpFlags.Normalised for i in ops):
            self.flags |= OpFlags.Normalised
        else:
            self.flags &= ~OpFlags.Normalised
        self._fixed = True

    def frozen(self) -> 'OpList':
        """Get an op list that is the frozen version of this"""
        if not self._fixed:
            self.fix()
        nl = OpList(*self.ops)
        nl._fixed = True # We did that just then, no need to do it twice
        nl.flags = self.flags & ~OpFlags.List # Every flag except List
        return nl
    def freeze(self) -> Self:
        """Freezes this op list and returns it"""
        if not self._fixed:
            self.fix()
        self.flags = self.flags & ~OpFlags.List
        return self

    def apply(self, mat: np.ndarray, arr: np.ndarray, crop, defSmth):
        if not self._fixed:
            self.fix() # Lazily fix it so it won't every new addition
        for op in self.ops:
            arr = op.apply(mat, arr, crop, defSmth)
        return arr

    def __add__(self, oth) -> 'OpList':
        if not self.flags & OpFlags.List:
            if oth.flags & OpFlags.List:
                return OpList(self, *oth.ops)
            return OpList(self, oth)
        if oth.flags & OpFlags.List:
            return OpList(*self.ops, *oth.ops)
        return OpList(*self.ops, oth)

    def __iter__(self):
        if not self._fixed:
            self.fix()
        return iter(self.ops)
    def flatten(self):
        if not self._fixed:
            self.fix()
        return self.ops

class TransOp(Op, _basey.Base, NormalisedBase):
    __slots__ = ['op', 'trans']
    def __new__(cls, op: Op, trans: Trans = None):
        if op.flags & OpFlags.Trans:
            if trans is None:
                return op
            if op.trans is None:
                return TransOp(op.op, trans)
            return TransOp(op.op, op.trans + trans)
        return super().__new__(cls)
    def __init__(self, op: Op, trans: Trans = None):
        self.op = op
        self.trans = trans
        self.flags = op.flags | OpFlags.Trans

    def apply(self, mat: np.ndarray, arr: np.ndarray, crop, defSmth):
        if self.trans is not None:
            args = self.trans.apply(mat, crop, defSmth)
            if args is None:
                return arr
            return self.op.apply(args[0], arr, *args[1:])
        return self.op.apply(mat, arr, crop, defSmth)

    def __iter__(self):
        return iter(self.op)
    def flatten(self):
        return self.op

    def rect(self):
        """Returns a tuple in the format (topleft_x, topleft_y, width, height)"""
        if self.trans is None:
            return self.op.rect()
        args = self.trans.apply(IDENTITY, (float("-inf"), float("-inf"), float("inf"), float("inf")), False)
        if args is None:
            return None, None, None, None
        r = self.op.rect()
        box = self._warpbbx(args[0], (r[0], r[1], r[2]+r[0],r[3]+r[1]), (0,0,0,0))
        return box[0], box[1], box[2]-box[0], box[3]-box[1]


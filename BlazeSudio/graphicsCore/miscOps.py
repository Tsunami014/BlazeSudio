from .base import Op, NormalisedOp, OpFlags, Vec2, Trans
from . import _basey, _blit, _calcs
from .core import _SurfaceBase
from PIL import Image as _PillowImg
from typing import overload
import numpy as np

__all__ = [
    'Overlay',
        'Fill',
    'Crop',
    'Surf',
        'Image',
        'Preserve'
]

class Overlay(Op):
    __slots__ = ['col']
    def __init__(self, col):
        """Overlays a colour on the screen (best used with transparency - if no transparency, use Fill instead)"""
        self.col = np.array(col, np.uint8)
        self.flags = OpFlags.NoFlags
    def apply(self, _, arr: np.ndarray, __, ___):
        _calcs.fill_arr(arr, self.col)
        return arr

class Fill(Overlay):
    __slots__ = []
    def __init__(self, col):
        """Will override all previous operations!! To include previous ops, use Overlay instead."""
        super().__init__(col)
        self.flags = OpFlags.Reset


class Crop(Trans, _basey.Base):
    __slots__ = ['pos', 'size']

    @overload
    def __init__(self,
            x: float, y: float, wid: float, hei: float,
            *, normalise_x = None, normalise_y = None):
        """Crop the sub-ops to the rect (x, y, wid, hei) (as a union with the parent crops)"""
    @overload
    def __init__(self, pos, sze,
            *, normalise_x = None, normalise_y = None):
        """Crop the sub-ops to the rect (pos, sze) (as a union with the parent crops)"""
    def __init__(self, *args, normalise_x = None, normalise_y = None):
        match len(args):
            case 2:
                r = [*args[0], *args[1]]
            case 4:
                r = list(args)
            case _:
                raise TypeError(
                    f'Incorrect number of arguments! Expected 2 or 4, found {len(args)}!'
                )
        self.pos = list(r[:2])
        if normalise_x is not None:
            self.pos[0] += r[2] * normalise_x
        if normalise_y is not None:
            self.pos[1] += r[3] * normalise_y
        self.size = (r[2]-r[0], r[3]-r[1])

    @property
    def rect(self):
        return *self.pos, *self.size
    @rect.setter
    def rect(self, new):
        self.pos = list(new[:2])
        self.size = list(new[2:])
    @property
    def topL(self):
        return self.pos
    @property
    def botR(self):
        return self.pos[0]+self.size[0], self.pos[1]+self.size[1]

    def apply(self, mat: np.ndarray, crop, defSmth: bool):
        newR = self._warpbbx(mat, (*self.pos, *self.botR), crop)
        if newR[2] == 0:
            return None
        return mat, newR, defSmth


class _ImageBase(NormalisedOp):
    """Must define _sze and arr in subclass"""
    __slots__ = ['_p', '_sze', 'arr']
    def __init__(self, **kwargs):
        self._p = Vec2(0, 0)
        self._cropop = Crop((0, 0), self._sze)
        NormalisedOp.__init__(self, **kwargs)
    @property
    def pos(self):
        return self._p
    @pos.setter
    def pos(self, *args):
        self._p = Vec2(*args)
    def apply(self, mat: np.ndarray, arr: np.ndarray, crop, defSmth):
        self._cropop.rect = (*self._p, *self._sze)
        args = self._cropop.apply(mat, crop, defSmth)
        if args is not None:
            mat, crop, defSmth = args
            _blit.blit(mat @ self._p.mat, self.arr, arr, crop)
        return arr

    def rect(self):
        return (*self._p, *self._sze)
    def _translate(self, *args):
        self._p += args

class Surf(_SurfaceBase, _ImageBase):
    """A surface for running operations on, allows ops to be cached"""
    @overload
    def __init__(self, wid: float, height: float, *, normalise_x = None, normalise_y = None): ...
    @overload
    def __init__(self, sze, *, normalise_x = None, normalise_y = None): ...
    def __init__(self, *args, **kwargs):
        match len(args):
            case 1:
                _SurfaceBase.__init__(self, args[0])
            case 2:
                _SurfaceBase.__init__(self, args)
            case _:
                raise TypeError(
                    f'Incorrect number of arguments! Expected 1 or 2, found {len(args)}!'
                )
        _ImageBase.__init__(self, **kwargs)

class Image(_ImageBase):
    __slots__ = ['_im', '_arr']
    def __init__(self, pth: str, *, normalise_x = None, normalise_y = None):
        self._arr = None
        self.image = _PillowImg.open(pth)
        super().__init__(normalise_x=normalise_x, normalise_y=normalise_y)

    @property
    def _sze(self):
        return self._im.size
    @property
    def arr(self):
        if self._arr is None:
            self._arr = np.asarray(self._im)
        return self._arr
    @property
    def image(self):
        return self._im
    @image.setter
    def image(self, new):
        self._arr = None
        if new.mode != 'RGBA':
            self._im = new.convert('RGBA')
        else:
            self._im = new

def Preserve(op: NormalisedOp) -> Surf:
    if not hasattr(op, 'rect'):
        raise ValueError(
            'Op is not normalised - it has no rect function!'
        )
    x, y, wid, hei = op.rect()
    if x is None:
        raise ValueError(
            'Op seems normalised but rect returns None!'
        )
    s = Surf(wid, hei)(op)
    s._p = x, y
    return s


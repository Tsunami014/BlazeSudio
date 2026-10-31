from .base import MatTrans
from typing import overload, Iterable
import math

__all__ = [
    'Transform',
    'Translate',
    'Rotate',
    'Scale',
    'Resize',
]

class Transform(MatTrans):
    def __init__(
        self, *,
        rotation = 0,
        translate = (0, 0),
        scale = (1, 1)
    ):
        if rotation == 0:
            cos = 1
            sin = 0
        else:
            cos = math.cos(rotation)
            sin = math.sin(rotation)

        super().__init__([
            [scale[0]*cos, -sin,         translate[0]],
            [sin,          scale[1]*cos, translate[1]],
            [0,            0,            1]
        ])

class Translate(MatTrans):
    @overload
    def __init__(self, pos: Iterable[int]): ...
    @overload
    def __init__(self, x: int, y: int): ...
    def __init__(self, *args):
        match len(args):
            case 1:
                x, y = args[0]
            case 2:
                x, y = args
            case _:
                raise TypeError(
                    f'Expected 1 or 2 arguments, found {len(args)}!'
                )
        super().__init__([
            [1, 0, x],
            [0, 1, y],
            [0, 0, 1]
        ])

class Rotate(MatTrans):
    def __init__(self, angle):
        if angle == 0:
            cos = 1
            sin = 0
        else:
            rads = math.radians(angle)
            cos = math.cos(rads)
            sin = math.sin(rads)
        super().__init__([
            [cos, -sin, 0],
            [sin, cos,  0],
            [0,   0,    1]
        ])

class Scale(MatTrans):
    @overload
    def __init__(self, sze: Iterable[int]): ...
    @overload
    def __init__(self, wid: int, hei: int): ...
    def __init__(self, *args):
        match len(args):
            case 2:
                sze = (args[0], args[1])
            case 1:
                sze = args[0]
                if len(sze) != 2:
                    raise TypeError(
                        f'Size must be an iterable with length 2, found length {len(sze)}!'
                    )
            case _:
                raise TypeError(
                    f'Expected 1 or 2 arguments, found {len(args)}!'
                )
        super().__init__([
            [sze[0], 0,      0],
            [0,      sze[1], 0],
            [0,      0,      1]
        ])

class Resize(Scale):
    @overload
    def __init__(self, fromsze: Iterable[int], tosze: Iterable[int]): ...
    @overload
    def __init__(self, fromwid: int, fromhei: int, towid: int, tohei: int): ...
    def __init__(self, *args):
        match len(args):
            case 2:
                f, t = args
            case 4:
                fw, fh, tw, th = args
                f, t = (fw, fh), (tw, th)
            case _:
                raise TypeError(
                    f'Expected 1 or 2 arguments, found {len(args)}!'
                )
        super().__init__(t[0]/f[0], t[1]/f[1])


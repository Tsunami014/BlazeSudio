from typing import overload, Iterable, Tuple
from .base import NormalisedOp
from . import _calcs
import numpy as np
import math

Point = Tuple[float, float]

class Polygon(NormalisedOp):
    __slots__ = ['ps', 'thickness', 'col', 'round']

    def rect(self):
        topLeft = [
            min(i[0] for i in self.ps),
            min(i[1] for i in self.ps),
        ]
        botRight = [
            max(i[0] for i in self.ps),
            max(i[1] for i in self.ps),
        ]
        return *topLeft, botRight[0]-topLeft[0], botRight[1]-topLeft[1]

    def _translate(self, x, y):
        self.ps += [x, y]

    def __init__(self,
            ps: Iterable[Point], thickness: float, col: np.ndarray,
                 *, round: bool = True, normalise_x = None, normalise_y = None):
        """
        Draw a closed polygon!

        Args:
            ps: The points making up the polygon
            thickness: The thickness of the line. Must be > 0.
            col: The colour of the line

        Keyword args:
            round: Whether the line ends are round or not
        """
        if thickness <= 0:
            raise ValueError(
                'Line has to have a thickness of greater than 0!'
            )
        self.ps = np.array(ps, float)
        assert len(self.ps.shape) == 2, "Points must be a 2 dimensional array; [(point 1 x, point 1 y), (point 2 x, point 2 y), etc.]"
        assert self.ps.shape[1] == 2, "Points must have only 2 dimensions; an x and a y; [(point 1 x, point 1 y), etc.]"
        assert thickness >= 0, "Thickness must be >=0"
        self.thickness = thickness
        self.col = np.array(col, np.uint8)
        assert self.col.shape == (4,), "Colour is of incorrect shape!"
        self.round = round
        super().__init__(normalise_x=normalise_x, normalise_y=normalise_y)
    
    def apply(self, mat: np.ndarray, arr: np.ndarray, crop, defSmth) -> np.ndarray:
        ps = self.ps
        if len(ps) < 2:
            return arr
        A = mat[:2, :2]
        sx2 = A[0,0]*A[0,0] + A[1,0]*A[1,0]
        sy2 = A[0,1]*A[0,1] + A[1,1]*A[1,1]
        t = self.thickness * ((sx2 + sy2) * 0.5) ** 0.5
        newps = self._warpPs(mat, ps)
        _calcs.drawPolyLine(arr, newps, t, self.col, crop, self.round)
        # TODO: Fill
        return arr

class Line(Polygon):
    @overload
    def __init__(self,
            p1: Point, p2: Point, thickness: float, col: np.ndarray,
            *, round: bool = True, normalise_x = None, normalise_y = None):
        """
        Draw a line!

        Args:
            p1: The starting point of the line (must be in format `[x, y]`)
            p2: The ending point of the line (must be in format `[x, y]`)
            thickness: The thickness of the line. Must be > 0.
            col: The colour of the line

        Keyword args:
            round: Whether the line ends are round or not
        """
    @overload
    def __init__(self,
            ps: Iterable[Point], thickness: float, col: np.ndarray,
            *, round: bool = True, normalise_x = None, normalise_y = None):
        """
        Draw a line!

        Args:
            ps: The points of the line (must be in format `[[x1, y1], [x2, y2]]`)
            thickness: The thickness of the line. Must be > 0.
            col: The colour of the line

        Keyword args:
            round: Whether the line ends are round or not
        """
    def __init__(self, *args, **kwargs):
        match len(args):
            case 4:
                p1, p2, thickness, col = args
                ps = (p1, p2)
            case 3:
                ps, thickness, col = args
            case _:
                raise TypeError(
                    f'Incorrect number of arguments! Expected 3 or 4, found {len(args)}!'
                )
        assert thickness > 0, "Thickness must be >0"
        super().__init__(ps, thickness, col, **kwargs)
        assert self.ps.shape == (2, 2), "Points must be in this format: [(point 1 x, point 1 y), (point 2 x, point 2 y)]"


class Rect(Polygon):
    __slots__ = ['pos', 'sze', 'roundness', 'col']

    def rect(self):
        return (*self.pos, *self.sze)

    def _translate(self, x, y):
        self.pos = [self.pos[0]+x, self.pos[1]+y]

    @overload
    def __init__(self,
            pos: Point, sze: Point, thickness: float, col: np.ndarray,
            *, roundness: float = 0, round: bool = True, normalise_x = None, normalise_y = None):
        """
        Draws a rectangle!

        Args:
            pos: The position of the rect
            sze: The size of the rect
            thickness: The thickness of the rect. If == 0, will fill the entire rect. Must be >= 0.
            col: The colour of the rect

        Keyword args:
            roundness: The roundness of the rect. 0 = ends of lines rounded, >0 = ends rounded by that many pixels, <0 = do not round the lines at all
            round: Whether to include circles at every joint of the line or not
        """
    @overload
    def __init__(self,
            x: float, y: float, width: float, height: float, thickness: float, col: np.ndarray,
            *, roundness: float = 0, round: bool = True, normalise_x = None, normalise_y = None):
        """
        Draws a rectangle!

        Args:
            x: The x position of the rect
            y: The y position of the rect
            width: The width of the rect
            height: The height of the rect
            thickness: The thickness of the rect. If == 0, will fill the entire rect. Must be >= 0.
            col: The colour of the rect

        Keyword args:
            roundness: The roundness of the rect. 0 = ends of lines rounded, >0 = ends rounded by that many pixels, <0 = do not round the lines at all (doesn't apply when using projection/rotation)
            round: Whether to include circles at every joint of the line or not (only applies when using projection/rotation)
        """
    def __init__(self, *args, roundness = 0, round=True, **kwargs):
        match len(args):
            case 4:
                self.pos, self.sze, self.thickness, col = args
            case 6:
                x, y, w, h, self.thickness, col = args
                self.pos = (x, y)
                self.sze = (w, h)
            case _:
                raise TypeError(
                    f'Incorrect number of arguments! Expected 4 or 6, found {len(args)}!'
                )
        assert self.thickness >= 0, "Thickness must be >=0"
        self.roundness = roundness
        self.col = np.array(col, np.uint8)
        assert self.col.shape == (4,), "Colour is of incorrect shape!"
        self.round = round
        NormalisedOp.__init__(self, **kwargs)

    @property
    def ps(self):
        return np.array([
            self.pos,
            [self.pos[0], self.pos[1]+self.sze[1]],
            [self.pos[0]+self.sze[0], self.pos[1]+self.sze[1]],
            [self.pos[0]+self.sze[0], self.pos[1]]
        ], float)

    def apply(self, mat: np.ndarray, arr: np.ndarray, crop, defSmth) -> np.ndarray:
        # Checks if the rectangle after matrix op is still a rectangle - i.e. no perspective warp or rotation
        if self._regMat(mat):
            if mat[0, 1] == 0 and mat[1, 0] == 0:
                sx = abs(mat[0, 0])
                sy = abs(mat[1, 1])
            else:
                sx = abs(mat[0, 1])
                sy = abs(mat[1, 0])
            t = self.thickness * 0.5 * (sx + sy)
            r = self.roundness * 0.5 * (sx + sy)

            p, s = self._regWarp(mat, self.pos), self._regWarp(mat, self.sze, False)
            _calcs.drawRect(arr, p, s, t, r, self.col, crop)
        else:
            # If not, draw the lines
            super().apply(mat, arr, crop, defSmth)
        return arr


# TODO: Add an input for rotation
class Elipse(NormalisedOp):
    __slots__ = ['pos', 'xradius', 'yradius', 'thickness', 'col']

    def rect(self):
        return self.pos[0]-self.xradius, self.pos[1]-self.yradius, self.xradius*2, self.yradius*2

    def _translate(self, x, y):
        self.pos = [self.pos[0]+x, self.pos[1]+y]

    @overload
    def __init__(self,
            pos: Point, xradius: float, yradius: float, thickness: float, col: np.ndarray,
            *, normalise_x = None, normalise_y = None):
        """
        Draws an elipse!

        Args:
            pos: The position of the elipse
            xradius: The radius of the width of the elipse
            yradius: The radius of the height of the elipse
            thickness: The thickness of the circle. If == 0, will fill the circle entirely. Must be >= 0.
            col: The colour to fill the circle with.
        """
    @overload
    def __init__(self,
            x: float, y: float, xradius: float, yradius: float, thickness: float, col: np.ndarray,
            *, normalise_x = None, normalise_y = None):
        """
        Draws an elipse! (recommended to use the other definition with `((x, y), ...)` instead of `(x, y, ...)` for readability)

        Args:
            x: The x position of the elipse
            y: The y position of the elipse
            xradius: The radius of the width of the elipse
            yradius: The radius of the height of the elipse
            thickness: The thickness of the circle. If == 0, will fill the circle entirely. Must be >= 0.
            col: The colour to fill the circle with.
        """
    def __init__(self, *args, **kwargs):
        match len(args):
            case 6:
                x, y, self.xradius, self.yradius, self.thickness, col = args
                self.pos = (x, y)
            case 5:
                self.pos, self.xradius, self.yradius, self.thickness, col = args
            case _:
                raise ValueError(
                    f'Expected 5 or 6 arguments, found {len(args)}!'
                )
        assert self.thickness >= 0, "Thickness must be >=0"
        self.col = np.array(col, np.uint8)
        assert self.col.shape == (4,), "Colour is of incorrect shape!"
        super().__init__(**kwargs)
    
    def apply(self, mat: np.ndarray, arr: np.ndarray, crop, defSmth) -> np.ndarray:
        if mat[2,2] != 1:
            raise NotImplementedError(
                'Cannot have a non-normalized homogeneous coordinate with circles yet!'
            )
        if mat[0,2] == 0 and mat[1,2] == 0:
            centre = self._regWarp(mat, self.pos)
            A = mat[:2, :2]
            u = A @ np.array([1.0, 0.0]) * self.xradius
            v = A @ np.array([0.0, 1.0]) * self.yradius

            r1 = np.hypot(u[0], u[1])
            r2 = np.hypot(v[0], v[1])

            sx2 = A[0,0]*A[0,0] + A[1,0]*A[1,0]
            sy2 = A[0,1]*A[0,1] + A[1,1]*A[1,1]
            t = self.thickness * ((sx2 + sy2) * 0.5) ** 0.5
            if r1 == r2:
                _calcs.drawCirc(arr, centre, r1, t, self.col, crop)
            else:
                angle = math.atan2(u[1], u[0])
                _calcs.drawElipse(arr, centre, r1, r2, angle, t, self.col, crop)
        else:
            raise NotImplementedError(
                'Cannot have projective transform with circles yet!'
            )
        return arr

class Circle(Elipse):
    @overload
    def __init__(self,
            pos: Point, radius: float, thickness: float, col: np.ndarray,
            *, normalise_x: float = 0, normalise_y: float = 0):
        """
        Draws a circle!

        Args:
            pos: The position of the circle
            radius: The radius of the circle
            thickness: The thickness of the circle. If == 0, will fill the circle entirely. Must be >= 0.
            col: The colour to fill the circle with.
        """
    @overload
    def __init__(self,
            x: float, y: float, radius: float, thickness: float, col: np.ndarray,
            *, normalise_x: float = 0, normalise_y: float = 0):
        """
        Draws a circle! (recommended to use the other definition with `((x, y), ...)` instead of `(x, y, ...)` for readability)

        Args:
            x: The X position of the circle
            y: The y position of the circle
            radius: The radius of the circle
            thickness: The thickness of the circle. If == 0, will fill the circle entirely. Must be >= 0.
            col: The colour to fill the circle with.
        """
    def __init__(self, *args, **kwargs):
        match len(args):
            case 5:
                x, y, radius, self.thickness, col = args
                self.pos = (x, y)
            case 4:
                self.pos, radius, self.thickness, col = args
            case _:
                raise ValueError(
                    f'Expected 4 or 5 arguments, found {len(args)}!'
                )
        assert self.thickness >= 0, "Thickness must be >=0"
        self.xradius, self.yradius = radius, radius
        self.col = np.array(col, np.uint8)
        assert self.col.shape == (4,), "Colour is of incorrect shape!"
        NormalisedOp.__init__(self, **kwargs)


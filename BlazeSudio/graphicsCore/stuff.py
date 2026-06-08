from typing import Tuple, overload
from collections import deque
import time

__all__ = ['Clock', 'AvgClock', 'Col']

class Clock():
    def __init__(self):
        self.dt = 0
        """The amount of seconds since the last tick"""
        self._lastTime = None

    def tick(self, maxfps: float = None):
        """
        Ticks the clock, updating FPS count and optionally enforcing a maximum FPS.

        Args:
            maxfps: The maximum fps the application should run at. Defaults to None (don't enforce)
        """
        t = time.perf_counter()
        slept = False
        if self._lastTime is not None:
            delta = t - self._lastTime
            if maxfps is not None:
                target_dt = 1.0 / maxfps
                target = target_dt - delta - 0.001
                if target > 0.1:
                    slept = True
                    time.sleep(target)
                    t = time.perf_counter()
                    delta = t - self._lastTime
            self.dt = delta
        if maxfps is not None and not slept:
            time.sleep(0)
        self._lastTime = t

    def get_fps(self):
        """
        Returns the number of frames per second instantly
        """
        return 0 if self.dt == 0 else 1.0 / self.dt

class AvgClock(Clock):
    def __init__(self, secs: float = 5):
        """
        An average Clock, averaging the fps over a set time.

        Args:
            secs: The number of seconds to average the fps over. Defaults to 5
        """
        self.secs = secs
        self._frameTimes = deque()
        super().__init__()

    def tick(self, maxfps: float = None):
        """
        Ticks the clock, updating FPS count and optionally enforcing a maximum FPS.

        Args:
            maxfps: The maximum fps the application should run at. Defaults to None (don't enforce)
        """
        super().tick(maxfps)
        # record this tick
        self._frameTimes.append(self._lastTime)
        # drop any frames older than time s
        cutoff = self._lastTime - self.secs
        while self._frameTimes and self._frameTimes[0] < cutoff:
            self._frameTimes.popleft()

    def get_fps(self):
        """
        Returns the average FPS over the last secs seconds.
        """
        count = len(self._frameTimes)
        if count == 0:
            return 0
        time = self._lastTime - self._frameTimes[0]
        return count / time if time > 0 else 0

    def get_fps_inst(self):
        """
        Returns the number of frames per second instantly
        """
        return super().get_fps()

def _rgb(*args): # To be able to see the colours here
    return *args, 255
class Col:
    """
    A Colour is an rgb tuple.
    
    This class gives some helper functions for creating these tuples based off of different colour types.
    """
    colourType = Tuple[int, int, int, int]
    _RGBHEXFMT = "#{0:02x}{1:02x}{2:02x}"
    # TODO: Different hex values (e.g. rgba hex or 3 char hex)
    
    @overload
    def __new__(cls, hex: str): ...
    @overload
    def __new__(cls, r: int, g: int, b: int, a: int = 255): ...
    def __new__(cls, *args):
        if len(args) == 1:
            return cls.hex(args[0])
        return cls.rgb(*args)

    @classmethod
    def rgb(cls, r: int, g: int, b: int, a: int = 255) -> colourType:
        return (r, g, b, a)
    @classmethod
    def rgba(cls, r: int, g: int, b: int, a: int) -> colourType:
        return (r, g, b, a)
    @classmethod
    def hex(cls, hex: str) -> colourType:
        val = int(hex.lstrip("#"), 16)
        r = (val >> 16) & 0xFF
        g = (val >> 8) & 0xFF
        b = val & 0xFF
        return (r, g, b, 255)
    @classmethod
    def hsv(cls, h: int, s: int, v: int, a: int = 255) -> colourType:
        if s == 0.0:
            return v, v, v

        h /= 60.0 # Sector 0 to 5
        i = int(h)
        f = h - i # Factorial part of h
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))

        if i == 0:
            return (v, t, p, a)
        if i == 1:
            return (q, v, p, a)
        if i == 2:
            return (p, v, t, a)
        if i == 3:
            return (p, q, v, a)
        if i == 4:
            return (t, p, v, a)
        return (v, p, q, a)
    @classmethod
    def hsva(cls, h: int, s: int, v: int, a: int) -> colourType:
        return cls.hsv(h, s, v, a)
    @classmethod
    def to_rgb(cls, col: colourType) -> Tuple[int, int, int]:
        return col[:3]
    @classmethod
    def to_rgba(cls, col: colourType) -> Tuple[int, int, int, int]:
        return col
    @classmethod
    def to_hex(cls, col: colourType, upper=True) -> str:
        def clamp(x):
            assert 0 <= x <= 255, "RGB value must be between 0-255!"
            return x
        o = cls._RGBHEXFMT.format(clamp(col[0]), clamp(col[1]), clamp(col[2]))
        if upper:
            return o.upper()
        return o
    @classmethod
    def to_hsv(cls, col: colourType) -> Tuple[int, int, int]:
        r, g, b = col[0] / 255.0, col[1] / 255.0, col[2] / 255.0
        mx = max(r, g, b)
        mn = min(r, g, b)
        diff = mx - mn

        v = mx
        s = 0 if mx == 0 else diff / mx
        h = 0
        if diff != 0:
            if mx == r:
                h = (60 * ((g - b) / diff) + 360) % 360
            elif mx == g:
                h = (60 * ((b - r) / diff) + 120) % 360
            elif mx == b:
                h = (60 * ((r - g) / diff) + 240) % 360

        return (h, s, v)
    @classmethod
    def to_hsva(cls, col: colourType) -> Tuple[int, int, int, int]:
        return (*cls.to_hsv(col), col[3])

    @classmethod
    def add_alpha(cls, col: colourType, a: int) -> colourType:
        return (col[0], col[1], col[2], max(min(col[3]+a, 255), 0))
    @classmethod
    def add_rgb(cls, col: colourType, r: int, g: int, b: int, a: int = 0) -> colourType:
        clamp = lambda val: max(min(val, 255), 0)
        return (clamp(col[0]+r), clamp(col[1]+g), clamp(col[2]+b), clamp(col[3]+a))
    @classmethod
    def add_rgba(cls, col: colourType, r: int, g: int, b: int, a) -> colourType:
        return cls.add_rgba(col, r, g, b, a)
    @classmethod
    def add_hsv(cls, col: colourType, h: int, s: int, v: int, a: int = 0) -> colourType:
        clamp = lambda val, mx: max(min(val, mx), 0)
        oh, os, ov = cls.to_hsv(col)
        return cls.hsv(
            clamp(oh+h, 360),
            clamp(os+s, 100),
            clamp(ov+v, 100),
            clamp(col[3]+a, 255),
        )
    @classmethod
    def add_hsva(cls, col: colourType, h: int, s: int, v: int, a: int) -> colourType:
        return cls.add_hsv(col, h, s, v, a)

    @classmethod
    def lighten(cls, col: colourType, amnt: int):
        """Increase the brightness of the colour by amnt (0-255)"""
        return cls.add_rgb(col, amnt, amnt, amnt)
    @classmethod
    def darken(cls, col: colourType, amnt: int):
        """Decrease the brightness of the colour by amnt (0-255)"""
        return cls.add_rgb(col, -amnt, -amnt, -amnt)

    TrueBlack = (0, 0, 0, 255)
    TrueGrey = (125, 125, 125, 255)
    TrueWhite = (255, 255, 255, 255)
    Transparent = (0, 0, 0, 0)

    Red = _rgb(237, 175, 184)
    Orange = _rgb(252, 208, 161)
    Yellow = _rgb(241, 227, 190)
    Green = _rgb(165, 201, 154)
    Blue = _rgb(145, 217, 250)
    Indigo = _rgb(187, 201, 252)
    Purple = _rgb(214, 194, 223)
    White = _rgb(250, 249, 240)
    LightGrey = _rgb(181, 182, 186)
    Grey = _rgb(121, 123, 132)
    Black = _rgb(35, 26, 28)

    Background = _rgb(250, 252, 252)
    Primary = _rgb(136, 107, 89)
    Secondary = _rgb(129, 95, 100)
    Accent = _rgb(87, 90, 75)


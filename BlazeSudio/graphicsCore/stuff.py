from typing import Tuple, overload
from collections import deque
import time

__all__ = ['Clock', 'AvgClock', 'Col']

class Clock():
    def __init__(self):
        self.dt = 0
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
            # raw delta-time
            delta = t - self._lastTime
            # enforce max FPS if requested
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
        self.goodEnough = False
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
            self.goodEnough = True
            self._frameTimes.popleft()

    def get_fps(self):
        """
        Returns the average FPS over the last secs seconds.
        """
        if not self.goodEnough:
            return self.get_fps_inst() # If the specified time hasn't passed, get the instant FPS
        count = len(self._frameTimes)
        return count / self.secs if self.secs > 0 else 0

    def get_fps_inst(self):
        """
        Returns the number of frames per second instantly
        """
        return super().get_fps()

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
    # TODO: to/from hsv

    Black = (0, 0, 0, 255)
    Grey = (125, 125, 125, 255)
    White = (255, 255, 255, 255)
    Transparent = (0, 0, 0, 0)
    # TODO: themes - repeated colours (and 'highlight 1', 'tone 3', etc.) put in a list so apps can easily theme switch


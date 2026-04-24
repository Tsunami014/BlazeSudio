from .base import Op, IDENTITY
from typing import overload, Iterable, Self

import numpy as np
import ctypes
import sdl2

__all__ = ['Core']


class _SurfaceBase:
    def __init__(self, sze):
        self._sze = sze
        self.op: Op|None = None
        self._cachedout = None
        self._cachedarr = None
        self.isSmooth = False

    @overload
    def resize(self, sze: Iterable[int] ,/):
        """
        Resize the surface

        Args:
            sze (Iterable[int]): The new size
        """
    @overload
    def resize(self, width: int, height: int ,/):
        """
        Resize the surface

        Args:
            width (int): The new width
            height (int): The new height
        """
    def resize(self, *args):
        match len(args):
            case 1:
                sze = args[0]
            case 2:
                sze = (args[0], args[1])
            case _:
                raise TypeError(
                    f'Too many arguments! Expected 1-2, found {len(args)}!'
                )

        if self._sze != sze:
            self._cachedout = None
            self._cachedarr = None
            self._sze = sze

    @property
    def size(self) -> Iterable[int]:
        return self._sze
    @size.setter
    def size(self, newSze):
        self.resize(newSze)

    def __call__(self, other: Op) -> Self:
        if self.op != other:
            self.op = other
            self._cachedout = None
        return self

    @property
    def arr(self) -> np.ndarray:
        if self._cachedout is None:
            if self._cachedarr is None:
                self._cachedarr = np.ndarray((self._sze[1], self._sze[0], 4), np.uint8) # User should fill with colour
            if self.op is not None:
                self._cachedout = self.op.apply(IDENTITY, self._cachedarr, (0, 0, *self._sze), self.isSmooth)
            else:
                self._cachedout = self._cachedarr
        return self._cachedout

    def clear(self) -> Self:
        self.op = None
        self._cachedout = None
        return self
    def clearsurf(self) -> Self:
        self._cachedarr = None
        return self
    def rough(self) -> Self:
        self.isSmooth = False
        return self
    def smooth(self) -> Self:
        self.isSmooth = True
        return self


_PIXFMT = sdl2.SDL_PIXELFORMAT_ABGR8888 # NOTE: This *may* display funny on big-endian systems
class _CoreCls(_SurfaceBase):
    def __new__(cls): # Incase someone weird gets ahold of this class
        if not hasattr(cls, '_instance'):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._mainWin = sdl2.SDL_CreateWindow(b"Blaze Sudio game", 
                        sdl2.SDL_WINDOWPOS_CENTERED, sdl2.SDL_WINDOWPOS_CENTERED, 0, 0, sdl2.SDL_WINDOW_SHOWN)
        self._renderer = sdl2.SDL_CreateRenderer(self._mainWin, -1,
            sdl2.SDL_RENDERER_ACCELERATED)
        self._texture = sdl2.SDL_CreateTexture(self._renderer, _PIXFMT, sdl2.SDL_TEXTUREACCESS_STREAMING, 0, 0)

        super().__init__((0, 0))

    def Quit(self):
        """
        Quits the application, handling all quit code accordingly
        """
        sdl2.SDL_DestroyRenderer(self._renderer)
        sdl2.SDL_DestroyWindow(self._mainWin)
        sdl2.SDL_Quit()

    @overload
    def resize(self):
        """
        Resize the window to fullscreen
        """
    @overload
    def resize(self, sze: Iterable[int]):
        """
        Resize the window. If resized to (0, 0), will become fullscreen.

        Args:
            sze (Iterable[int]): The size of the new window
        """
    @overload
    def resize(self, width: int, height: int ,/):
        """
        Resize the window. If resized to (0, 0), will become fullscreen.

        Args:
            width (int): The width of the new window
            height (int): The height of the new window
        """
    def resize(self, *args):
        if len(args) == 0:
            args = (0, 0)
        super().resize(*args)
        if self._sze[0] == 0 and self._sze[1] == 0:
            sdl2.SDL_SetWindowFullscreen(self._mainWin, sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP)
            w, h = ctypes.c_int(), ctypes.c_int()
            sdl2.SDL_GetWindowSize(self._mainWin, ctypes.byref(w), ctypes.byref(h))
            self._sze = (w.value, h.value)
        else:
            sdl2.SDL_SetWindowSize(self._mainWin, *self._sze)

        sdl2.SDL_DestroyTexture(self._texture)
        self._texture = sdl2.SDL_CreateTexture(self._renderer, _PIXFMT, sdl2.SDL_TEXTUREACCESS_STREAMING, *self._sze)

    def rend(self):
        """
        Render the entire screen.
        """
        sdl2.SDL_UpdateTexture(
            self._texture,
            None,
            self.arr.ctypes.data,
            self._sze[0]*4
        )

        sdl2.SDL_RenderCopy(self._renderer, self._texture, None, None)
        sdl2.SDL_RenderPresent(self._renderer)


    def set_title(self, title: str):
        """
        Set the title of the window

        Args:
            title (str): The new title of the window
        """
        sdl2.SDL_SetWindowTitle(self._mainWin, title.encode("utf-8"))
    def set_icon(self, icon: Op):
        pass # TODO: This
        #icon = sdlimage.IMG_Load(b"icon.png")
        #sdl2.SDL_SetWindowIcon(self._mainWin, icon)
        #sdl2.SDL_FreeSurface(icon)

Core = _CoreCls()


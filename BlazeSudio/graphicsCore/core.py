from .base import Op, IDENTITY
from typing import overload, Iterable, Self

import numpy as np
import ctypes
import sdl2

__all__ = ['Core']


_PIXFMT = sdl2.SDL_PIXELFORMAT_ABGR8888 # NOTE: This *may* display funny on big-endian systems
class _CoreCls:
    def __new__(cls): # Incase someone weird gets ahold of this class
        if not hasattr(cls, '_instance'):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_init", False):
            return
        self._init = True

        self._mainWin = sdl2.SDL_CreateWindow(b"Blaze Sudio game",
                            sdl2.SDL_WINDOWPOS_CENTERED, sdl2.SDL_WINDOWPOS_CENTERED, 800, 500,
                            sdl2.SDL_WINDOW_SHOWN)
        self._renderer = sdl2.SDL_CreateRenderer(self._mainWin, -1,
            sdl2.SDL_RENDERER_ACCELERATED)
        self._texture = sdl2.SDL_CreateTexture(self._renderer, _PIXFMT, sdl2.SDL_TEXTUREACCESS_STREAMING, 800, 500)

        self._arr = None
        self._sze = (800, 500)
        self.op: Op|None = None
        self.smooth = False

    def Quit(self):
        """
        Quits the application, handling all quit code accordingly.

        This is useful to include at the end of your program as it closes the window much faster than if you don't include it.
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
        match len(args):
            case 0:
                sze = (0, 0)
            case 1:
                sze = args[0]
            case 2:
                sze = (args[0], args[1])
            case _:
                raise TypeError(
                    f'Too many arguments! Expected 1-2, found {len(args)}!'
                )
        if sze[0] == 0 and sze[1] == 0:
            sdl2.SDL_SetWindowFullscreen(self._mainWin, sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP)
            w, h = ctypes.c_int(), ctypes.c_int()
            sdl2.SDL_GetWindowSize(self._mainWin, ctypes.byref(w), ctypes.byref(h))
            sze = (w.value, h.value)
        else:
            sdl2.SDL_SetWindowSize(self._mainWin, *sze)
        self._sze = sze

        if self._arr is not None:
            sdl2.SDL_UnlockTexture(self._texture)
            self._arr = None
        sdl2.SDL_DestroyTexture(self._texture)
        self._texture = sdl2.SDL_CreateTexture(self._renderer, _PIXFMT, sdl2.SDL_TEXTUREACCESS_STREAMING, *self._sze)

    def __del__(self):
        if self._arr is not None:
            sdl2.SDL_UnlockTexture(self._texture)

    @property
    def size(self) -> Iterable[int]:
        return self._sze
    @size.setter
    def size(self, newSze):
        self.resize(newSze)

    @property
    def width(self) -> int: return self._sze[0]
    @property
    def height(self) -> int: return self._sze[1]

    @property
    def resizable(self) -> bool:
        flags = sdl2.SDL_GetWindowFlags(self._mainWin)
        return bool(flags & sdl2.SDL_WINDOW_RESIZABLE)
    @resizable.setter
    def resizable(self, new: bool):
        if self.resizable == new:
            return
        # Rebuild entire window because otherwise it won't work :(

        w, h = ctypes.c_int(), ctypes.c_int()
        x, y = ctypes.c_int(), ctypes.c_int()
        sdl2.SDL_GetWindowSize(self._mainWin, ctypes.byref(w), ctypes.byref(h))
        sdl2.SDL_GetWindowPosition(self._mainWin, ctypes.byref(x), ctypes.byref(y))
        flags = sdl2.SDL_GetWindowFlags(self._mainWin)
        if new:
            flags |= sdl2.SDL_WINDOW_RESIZABLE
        else:
            flags &= ~sdl2.SDL_WINDOW_RESIZABLE

        sdl2.SDL_DestroyTexture(self._texture)
        sdl2.SDL_DestroyRenderer(self._renderer)
        sdl2.SDL_DestroyWindow(self._mainWin)


        self._mainWin = sdl2.SDL_CreateWindow(
            sdl2.SDL_GetWindowTitle(self._mainWin) or b"Blaze Sudio game", 
            x.value, y.value, w.value, h.value, flags
        )
        self._renderer = sdl2.SDL_CreateRenderer(
            self._mainWin, -1, sdl2.SDL_RENDERER_ACCELERATED
        )
        self._texture = sdl2.SDL_CreateTexture(
            self._renderer, _PIXFMT, sdl2.SDL_TEXTUREACCESS_STREAMING, *self._sze
        )

    def _resize_event(self, event):
        self.resize(event.window.data1, event.window.data2)
        self.rend()

    def rend(self):
        """
        Render the entire screen by writing directly to SDL memory.
        """
        if self.op is None:
            sdl2.SDL_RenderClear(self._renderer)
            sdl2.SDL_RenderPresent(self._renderer)
            return

        if self._arr is None:
            pixels = ctypes.c_void_p()
            pitch  = ctypes.c_int()
            sdl2.SDL_LockTexture(self._texture, None, ctypes.byref(pixels), ctypes.byref(pitch))
            raw = (ctypes.c_uint8 * (self._sze[1] * pitch.value)).from_address(pixels.value)
            self._arr = (np.ndarray(
                shape=(self._sze[1], self._sze[0], 4),
                dtype=np.uint8,
                buffer=raw,
                strides=(pitch.value, 4, 1),
            ), pixels.value)

        self.op.apply(IDENTITY, self._arr[0], (0, 0, *self._sze), self.smooth)

        sdl2.SDL_UnlockTexture(self._texture)
        sdl2.SDL_RenderCopy(self._renderer, self._texture, None, None)
        sdl2.SDL_RenderPresent(self._renderer)
        pixels = ctypes.c_void_p()
        pitch = ctypes.c_int()
        sdl2.SDL_LockTexture(self._texture, None, ctypes.byref(pixels), ctypes.byref(pitch))
        if pixels.value != self._arr[1]:
            self._arr = None # Rebuild

    def clear(self):
        self.op = None
        self._arr = None
    def redraw(self):
        self._arr = None

    def __call__(self, other: Op) -> Self:
        if self.op != other:
            self.op = other
            self._arr = None
        return self

    @property
    def title(self) -> str:
        return sdl2.SDL_GetWindowTitle(self._mainWin).decode("utf-8")
    @title.setter
    def title(self, title):
        sdl2.SDL_SetWindowTitle(self._mainWin, title.encode("utf-8"))
    def set_icon(self, icon: Op):
        pass # TODO: This
        #icon = sdlimage.IMG_Load(b"icon.png")
        #sdl2.SDL_SetWindowIcon(self._mainWin, icon)
        #sdl2.SDL_FreeSurface(icon)

Core = _CoreCls()


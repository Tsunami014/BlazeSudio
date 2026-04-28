import freetype
import numpy as np
from typing import Self
from dataclasses import dataclass
from functools import lru_cache
from .base import NormalisedOp, Vec2
from .Trans import Translate
from . import _blit
import platform
import os

__all__ = [
    'SysFonts', 'Font'
]

@dataclass
class FChar:
    bitmap: np.ndarray
    advance: float
    width: float
    xoffs: float
    yoffs: float

class SysFonts:
    __slots__ = []
    _fs: object
    _def: object

    EXTRA_FONT_DIRS = []

    @classmethod
    def _iter_fonts(cls):
        sys = platform.system()
        if sys == "Windows":
            li = [
                os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts"),
            ]
        elif sys == "Darwin": # macOS
            li = [
                "/System/Library/Fonts",
                "/Library/Fonts",
                os.path.expanduser("~/Library/Fonts"),
            ]
        else: # Linux/Unix
            # Imagine not being on Linux where the fonts are auto-found
            import subprocess
            output = subprocess.check_output(["fc-list", ":", "file"], text=True)
            yield from [ln.split(':')[0] for ln in output.splitlines()]
            li = []

        for directory in li+cls.EXTRA_FONT_DIRS:
            if not os.path.exists(directory):
                continue

            for root, _, files in os.walk(directory):
                for f in files:
                    yield os.path.join(root, f)

    @classmethod
    def get_all(cls) -> dict[str, str]:
        """Returns a mapping of font names to their location"""
        if getattr(cls, '_fs', None) is None:
            cls._fs = dict()
            for f in cls._iter_fonts():
                if f.lower().endswith((".ttf", ".otf")):
                    cls._fs[f[f.rindex('/')+1:f.rindex('.')]] = f
        if len(cls._fs) == 0:
            raise ValueError(
                'No fonts were found on this system!'
            )
        return cls._fs
    @classmethod
    def clear(cls):
        """Clears the cached mapping of font names to their locations"""
        cls._fs = None
    @classmethod
    def __getitem__(cls, it: str) -> str|None:
        """Get the location of a specific font by its name"""
        if os.path.exists(it):
            return it
        return cls.get_all().get(it, None)
    @classmethod
    def pick_path(cls, *options) -> str|None:
        """Pick the first provided font name that exists and return the name"""
        li = cls.get_all()
        for opt in options:
            if opt in li or os.path.exists(opt):
                return opt
        return None
    @classmethod
    def pick(cls, *options) -> 'Font':
        """Pick the first provided font that exists and return the Font object (will use default if none found)"""
        return Font(cls.pick_path(*options))
    @classmethod
    def default_path(cls) -> str|None:
        """Gets the 'default' font path (the first one found on the system)"""
        li = cls.get_all()
        return li[list(li.keys())[0]]
    @classmethod
    def default(cls) -> 'Font':
        """Gets the 'default' font as a Font object (the first one found on the system)"""
        return Font(cls.default_path())

class _FontDrawOp(NormalisedOp):
    __slots__ = ['_p', 'font', 'text', 'col', '_cache', '_cachehash']
    def __init__(self, f, txt, col, **kwargs):
        self._p = Vec2(0, 0)
        self.font = f
        self.text = txt
        self.col = col
        self._cache = None
        self._cachehash = None
        super().__init__(**kwargs)
    @property
    def size(self):
        return self.font.linesize(self.text)

    def rect(self):
        return (*self._p, *self.size)
    def _translate(self, *args):
        self._p += args

    def apply(self, mat: np.ndarray, arr: np.ndarray, crop, defSmth):
        newcache = hash((self.text, self.font))
        if self._cache is None or self._cachehash != newcache:
            self._cachehash = newcache
            # TODO: Font caching, but only cache when the same text is used more than once in a row to prevent the longer cache routine running constantly
        self.font.load(self.text)
        xoffs = self._p.x
        yoffs = self._p.y + self.font.yoffs
        for c in self.text:
            char = self.font.cache[c]
            args = Translate(
                    xoffs + char.xoffs, char.yoffs + yoffs
                ).apply(mat, crop, defSmth)
            if args is not None:
                shp = char.bitmap.shape
                assert len(self.col) == 4, "Colour must contain 4 numbers"
                arrs = []
                for idx, c in enumerate(self.col[:-1]):
                    found = self.col.index(c)
                    if idx == found:
                        arrs.append(np.full(shp, c, dtype=np.uint8))
                    else:
                        arrs.append(arrs[found])
                arrs.append((char.bitmap*(self.col[-1]/255)).clip(0, 255).astype(np.uint8))
                _blit.blit(args[0], np.stack(arrs, axis=-1), arr, args[1])
            xoffs += char.advance
        return arr

class Font:
    __slots__ = ["face", "_pth", "cache"]
    def __init__(self, path: str|None = None, sze: float = 24):
        self.fontpth = path
        self.size = sze

    @property
    def size(self) -> int:
        return self.face.size.y_ppem
    @size.setter
    def size(self, size: int):
        self.face.set_pixel_sizes(0, size)
    def set_size_pt(self, size: float):
        self.face.set_char_size(size * 64)
        return self

    @property
    def fontpth(self) -> str:
        return self._pth
    @fontpth.setter
    def fontpth(self, newpth: str):
        pth = newpth or SysFonts.default_path()
        if not os.path.exists(pth):
            raise FileNotFoundError(
                f"Font file {pth} does not exist!"
            )
        self.face = freetype.Face(pth)
        self._pth = pth
        self.cache = dict()

    @property
    def family_name(self) -> str:
        return self.face.family_name

    def load(self, txt) -> None:
        for char in txt:
            if char in self.cache:
                continue
            self.face.load_char(char, freetype.FT_LOAD_RENDER)
            glyph = self.face.glyph
            h, w = glyph.bitmap.rows, glyph.bitmap.width
            self.cache[char] = FChar(
                np.array(glyph.bitmap.buffer, dtype=np.uint8).reshape(h, w),
                glyph.advance.x / 64, w, glyph.bitmap_left, -glyph.bitmap_top
            )

    @lru_cache()
    def __call__(self, txt, col: np.ndarray, *, normalise_x = None, normalise_y = None) -> _FontDrawOp:
        """Returns an Op that will draw the provided text using this font"""
        return _FontDrawOp(self, txt, col, normalise_x=normalise_x, normalise_y=normalise_y)
    def render(self, txt, col: np.ndarray, *, normalise_x = None, normalise_y = None) -> _FontDrawOp:
        """Returns an Op that will draw the provided text using this font"""
        return self(txt, col, normalise_x=normalise_x, normalise_y=normalise_y)

    @property
    def yoffs(self) -> float:
        return self.face.size.ascender / 64
    @property
    def lineheight(self) -> float:
        return self.face.size.height / 64
    def linewidth(self, txt) -> float:
        if txt == "":
            return 0
        self.load(txt)
        return sum(
            self.cache[i].advance for i in txt[:-1]
        )+self.cache[txt[-1]].width + 1
    def linesize(self, txt) -> float:
        return (
            self.linewidth(txt),
            self.lineheight,
        )


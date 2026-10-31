import freetype
import numpy as np
from dataclasses import dataclass
from functools import lru_cache
from .base import NormalisedOp, Vec2
from .Trans import Translate
from . import _blit
import platform
import os

from typing import overload
from collections.abc import Callable, Iterable

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

_WEIGHT_KEYWORDS = {
    'extrablack': 'black', 'ultrablack': 'black', 'black': 'black', 'heavy': 'black',
    'extrabold': 'extrabold', 'ultrabold': 'extrabold',
    'semibold': 'semibold', 'demibold': 'semibold',
    'bold': 'bold',
    'medium': 'medium',
    'extralight': 'extralight', 'ultralight': 'extralight',
    'light': 'light',
    'thin': 'thin', 'hairline': 'thin',
    'regular': 'regular', 'normal': 'regular', 'book': 'regular', 'roman': 'regular',
}


@dataclass(frozen=True)
class FontInfo:
    """Metadata describing a single font file installed on the system, used by
    SysFonts to select fonts by properties rather than by filename."""
    path: str
    family: str
    style: str
    italic: bool
    bold: bool
    weight: str
    monospace: bool
    scalable: bool
    condensed: bool

class SysFonts:
    EXTRA_FONT_DIRS = []
    _fonts_cache = None
    _default_override = None
    _default = None

    _PREFERRED_TRAITS = {
        'italic': (False, 3),
        'bold': (False, 2),
        'weight': ('regular', 2),
        'monospace': (False, 3),
        'condensed': (False, 1),
        'scalable': (True, 1),
    }

    @overload
    def __new__(cls,
                families: str | Iterable[str] | None = None,
                *,
                italic: bool | None = None,
                bold: bool | None = False,
                weight: str | None = None,
                monospace: bool | None = None,
                scalable: bool | None = None,
                condensed: bool | None = None,
                exclude_families: str | Iterable[str] | None = None,
                name_contains: str | None = None,
                where: Callable[[FontInfo], bool] | None = None,
                sze: float = 24) -> 'Font':
        ...
    def __new__(cls, families=None, *, sze=24, **kwargs):
        path = cls._pick_path(families=families, **kwargs)
        if path is None:
            path = cls.default_path()
        return Font(path, sze=sze)

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
    def _load_info(cls, path: str) -> FontInfo | None:
        """Opens a font file just far enough to read its metadata (no glyphs loaded)"""
        def _decode(x) -> str:
            """freetype-py hands back bytes for name fields - normalise to str"""
            if isinstance(x, bytes):
                return x.decode('utf-8', 'ignore')
            return x or ""
        try:
            face = freetype.Face(path)
        except Exception:
            return None
        family = _decode(face.family_name)
        if not family:
            return None
        style = _decode(face.style_name)
        style_flags = face.style_flags
        face_flags = face.face_flags
        style_lower = style.lower()
        is_bold = bool(style_flags & freetype.FT_STYLE_FLAG_BOLD)
        # FT_STYLE_FLAG_ITALIC misses "Oblique" styles in some fonts, so also keyword-match
        is_italic = bool(style_flags & freetype.FT_STYLE_FLAG_ITALIC) \
            or 'italic' in style_lower or 'oblique' in style_lower

        hay = f"{style} {family}".lower()
        for kw, canon in _WEIGHT_KEYWORDS.items():
            if kw in hay:
                wei = canon
                break
        else:
            wei = 'bold' if is_bold else 'regular'

        is_monospace = bool(face_flags & freetype.FT_FACE_FLAG_FIXED_WIDTH) \
            or 'mono' in hay or 'monospace' in hay

        return FontInfo(
            path=path,
            family=family,
            style=style,
            italic=is_italic,
            bold=is_bold,
            weight=wei,
            monospace=is_monospace,
            scalable=bool(face_flags & freetype.FT_FACE_FLAG_SCALABLE),
            condensed=any(k in style_lower for k in ('condensed', 'narrow', 'compressed')),
        )

    @classmethod
    def _all_fonts(cls) -> list[FontInfo]:
        if cls._fonts_cache is None:
            seen = set()
            infos = []
            for path in cls._iter_fonts():
                if not path.lower().endswith((".ttf", ".otf", ".ttc")):
                    continue
                if path in seen:
                    continue
                seen.add(path)
                info = cls._load_info(path)
                if info is not None:
                    infos.append(info)
            infos.sort(key=lambda i: (i.family.lower(), i.style.lower()))
            cls._fonts_cache = infos
        if len(cls._fonts_cache) == 0:
            raise ValueError(
                'No fonts were found on this system!'
            )
        return cls._fonts_cache

    @classmethod
    def clear(cls):
        """Clears the cached font metadata, forcing the next lookup to rescan the system"""
        cls._fonts_cache = None
    @classmethod
    def list_fonts(cls) -> list[FontInfo]:
        """Returns metadata for every font discovered on the system"""
        return list(cls._all_fonts())

    @staticmethod
    def _matches(info: FontInfo, families, italic=None, bold=None, weight=None, monospace=None,
                scalable=None, condensed=None, exclude_families=None, name_contains=None,
                where=None) -> bool:
        if families is not None:
            fams = {families.lower()} if isinstance(families, str) else {f.lower() for f in families}
            if info.family.lower() not in fams:
                return False
        if exclude_families is not None:
            exf = {exclude_families.lower()} if isinstance(exclude_families, str) else {f.lower() for f in exclude_families}
            if info.family.lower() in exf:
                return False

        if any(wanted is not None and wanted != actual for wanted, actual in (
            (italic, info.italic),
            (bold, info.bold),
            (monospace, info.monospace),
            (scalable, info.scalable),
            (condensed, info.condensed),
        )):
            return False

        if weight is not None and info.weight != _WEIGHT_KEYWORDS.get(weight.lower(), ''):
            return False
        if name_contains is not None:
            needle = name_contains.lower()
            if needle not in info.family.lower() and needle not in info.style.lower():
                return False
        if where is not None and not where(info):
            return False
        return True

    @classmethod
    def _pick_path(cls, families=None, **kwargs) -> str | None:
        if isinstance(families, str) and os.path.exists(families):
            return families
        best_path, best_distance = None, None
        for info in cls._all_fonts():
            if not cls._matches(info, families, **kwargs):
                continue
            distance = sum(
                sco if getattr(info, trait) != preferred else 0
                for trait, (preferred, sco) in cls._PREFERRED_TRAITS.items()
            )
            if distance == 0:
                return info.path
            if best_distance is None or distance < best_distance:
                best_path, best_distance = info.path, distance
        return best_path

    @classmethod
    @overload
    def set_default(cls,
                     families: str | Iterable[str] | None = None,
                     *,
                     italic: bool | None = None,
                     bold: bool | None = None,
                     weight: str | None = None,
                     monospace: bool | None = None,
                     scalable: bool | None = None,
                     condensed: bool | None = None,
                     exclude_families: str | Iterable[str] | None = None,
                     name_contains: str | None = None,
                     where: Callable[[FontInfo], bool] | None = None) -> None:
        """
        Sets the default font used everywhere a font of `None` is requested.

        Call with no arguments at all to reset back to the ordinary system default.

        If it doesn't work it may be because your criteria was too specific and it couldn't find a matching font.
        """
    @classmethod
    def set_default(cls, families=None, **kwargs):
        if families is None and (not kwargs or all(v is None for v in kwargs.values())):
            cls._default_override = None
            return
        path = cls._pick_path(families=families, **kwargs)
        if path is None:
            cls._default_override = None
        else:
            cls._default_override = path

    @classmethod
    def default_path(cls) -> str:
        """Gets the path of the current default font, unless overridden with `set_default`"""
        if cls._default_override is not None:
            return cls._default_override
        if cls._default is None:
            cls._default = cls._pick_path()
            if cls._default is None:
                cls._default = cls._all_fonts()[0].path
        return cls._default
    @classmethod
    def default(cls) -> 'Font':
        """Gets the current default font as a Font object"""
        return Font(cls.default_path())


class _FontDrawOp(NormalisedOp):
    __slots__ = ['_p', 'font', 'text', 'col', 'aligns', '_cache', '_cachehash']
    def __init__(self, f, txt, col, aligns, **kwargs):
        self._p = Vec2(0, 0)
        self.font = f
        self.text = txt
        self.col = col
        self.aligns = aligns
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
        yoffs = self._p.y + self.font.yoffs
        xoffs = self._p.x + (self.aligns[0] if len(self.aligns) > 0 else 0)
        lne = 0
        for c in self.text:
            if c == '\n':
                lne += 1
                xoffs = self._p.x + (self.aligns[lne] if len(self.aligns) > lne else 0)
                yoffs += self.font.lineheight
                continue
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
        self.cache = dict()
    def set_size_pt(self, size: float):
        self.face.set_char_size(size * 64)
        self.cache = dict()
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
            if char == '\n':
                continue
            if char in self.cache:
                continue
            self.face.load_char(char, freetype.FT_LOAD_RENDER)
            glyph = self.face.glyph
            h, w = glyph.bitmap.rows, glyph.bitmap.width
            self.cache[char] = FChar(
                np.array(glyph.bitmap.buffer, dtype=np.uint8).reshape(h, w),
                glyph.advance.x / 64, w, glyph.bitmap_left, -glyph.bitmap_top
            )

    def _get_list(self, txt, maxwid, breakOnSpace=True):
        if not txt:
            return []
        self.load(txt)
        extent = lambda ch: self.cache[ch].xoffs + self.cache[ch].width
        advs = [(i, self.cache[i].advance, extent(i)) if i != '\n' else (i,0,0) for i in txt[:-1]] + \
                [((c:=txt[-1]), (ext:=extent(c)), ext)]
        if breakOnSpace:
            advs2 = []
            txt = ""
            wid = 0
            lastdiff = 0
            for c, a, w in advs:
                if c in ('\n', ' ') or wid+w >= maxwid:
                    if c == ' ':
                        advs2.append((txt+' ', wid+a, wid+w))
                    else:
                        advs2.append((txt, wid, wid+lastdiff))
                    txt = ""
                    wid = 0
                    lastdiff = 0
                    if c == '\n':
                        advs2.append(('\n', None, None))
                        continue
                    if c == ' ':
                        continue
                txt += c
                wid += a
                lastdiff = w-a
            if txt:
                advs2.append((txt, wid, wid+lastdiff))
            advs = advs2
        outs = [[0, []]]
        lastdiff = 0
        for ad in advs:
            txt, a, w = ad
            if txt == '\n' or outs[-1][0]+w >= maxwid:
                outs[-1][0] += lastdiff
                outs.append([0, []])
                lastdiff = 0
            if txt != '\n':
                outs[-1][0] += a
                outs[-1][1].append(ad)
                lastdiff = w-a
        outs[-1][0] += lastdiff
        return [(wid, "".join(i[0] for i in ads) if ads else "") for wid, ads in outs]

    @lru_cache()
    def __call__(self, txt, col: np.ndarray, maxwid: int = None, breakOnSpace: bool = True, align: float = 0, *, normalise_x = None, normalise_y = None) -> _FontDrawOp:
        """Returns an Op that will draw the provided text using this font"""
        if maxwid is not None:
            li = self._get_list(txt, maxwid, breakOnSpace)
            txt = '\n'.join(i[1] for i in li)
            aligns = [max((maxwid-i[0])*align, 0) for i in li]
        else:
            aligns = []
        return _FontDrawOp(self, txt, col, aligns, normalise_x=normalise_x, normalise_y=normalise_y)
    def render(self, txt, col: np.ndarray, maxwid: int = None, breakOnSpace: bool = True, align: float = 0, *, normalise_x = None, normalise_y = None) -> _FontDrawOp:
        """Returns an Op that will draw the provided text using this font"""
        return self(txt, col, maxwid, breakOnSpace, align, normalise_x=normalise_x, normalise_y=normalise_y)

    @property
    def yoffs(self) -> float:
        return self.face.size.ascender / 64
    @property
    def lineheight(self) -> float:
        return self.face.size.height / 64
    def linewidth(self, txt) -> float:
        if txt == "":
            return 0
        if '\n' in txt:
            return max(self.linewidth(i) for i in txt.split('\n'))
        self.load(txt)
        # The line's true width is the furthest any glyph's bitmap actually
        # reaches to the right - not just the sum of advances, and not just the
        # last glyph's bitmap width. For most glyphs `advance >= xoffs + width`
        running = 0.0
        maxw = 0.0
        for ch in txt:
            c = self.cache[ch]
            reach = running + c.xoffs + c.width
            if reach > maxw:
                maxw = reach
            running += c.advance
        return maxw
    def linesize(self, txt) -> tuple[float, float]:
        return (
            self.linewidth(txt),
            self.lineheight * (txt.count('\n')+1),
        )

    def linesize_wid(self, txt, maxwid, breakOnSpace=True) -> tuple[float, float]:
        if txt == "":
            return (0, 0)
        wids = [i[0] for i in self._get_list(txt, maxwid, breakOnSpace)]
        return (max(wids)+1, len(wids)*self.lineheight)

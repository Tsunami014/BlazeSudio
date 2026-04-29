"""
The module for handling interaction

To update the interaction state, `update` or `updateLoop` or `handleBasic` must be called. They must be called preferably once per frame, as any less and the OS will question the window and any more and some events will get deleted.
"""
from . import _specialkeys
from .core import Core
from .Events import EvTyp, Event, KeyEvent, EVENT_LIST, EVENT_NAMES, _translateEv
from typing import Iterable
import sdl2
import sdl2.ext

for cls in EVENT_LIST:
    globals()[cls.__name__] = cls

__all__ = [
    'EvTyp',
    'Event',
    *EVENT_NAMES,
    'Keys',
    'update',
]

def __getattr__(name):
    import importlib
    import sys
    if name in __all__:
        mod = importlib.import_module(f".{name}", __name__)
        setattr(sys.modules[__name__], name, mod)
        return mod
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

class _KeysMeta(type):
    def __getitem__(cls, key):
        return cls._getit(key)

class Keys(metaclass=_KeysMeta):
    """
    Get keys pressed or key events

    - Is a key pressed? Use e.g. `Keys["a"]` (note this does not differentiate against 'A' and 'a')
    - Has a key event happened? Use the `Keys.event` function
    - Are any keyboard modifiers pressed? Use the booleans starting with `m` - e.g. `Keys.mShift`, `Keys.mCtrl` or `Keys.mAlt`
    """
    _kbdState: object
    _keyEvs: Iterable[Event] = []
    mShift: bool
    mCtrl: bool
    mAlt: bool
    mGui: bool
    """'Windows'/'Command'/'Super' key"""
    mNumLock: bool
    mCapsLock: bool
    @classmethod
    def _getit(cls, key):
        ln = len(key)
        if ln == 0:
            raise ValueError(
                'No input provided!'
            )
        lk = key.lower()
        k = _specialkeys.speshs.get(key, None)
        if k is None and ln == 1:
            k = sdl2.SDL_GetScancodeFromKey(ord(lk))
        if k == 0 or k is None:
            raise ValueError(
                f'No key found for "{lk}"'
            )
        return cls._kbdState[k]

    @classmethod
    def events(cls): pass # TODO: This, and also have lots of optional filters

class Mouse:
    """
    Get mouse buttons/movement

    - Is a mouse button pressed? Use e.g. `Mouse.left`
    - Mouse position? Use `Mouse.pos`, `Mouse.x` or `Mouse.y`
    - Set the mouse position? Use e.g. `Mouse.x = 10` (can set x, y or pos)
    """
    left: bool
    l: bool
    """Short for Mouse.left"""
    middle: bool
    m: bool
    """Short for Mouse.middle"""
    right: bool
    r: bool
    """Short for Mouse.right"""
    x1: bool
    """Extra button 1"""
    x2: bool
    """Extra button 2"""
    _pos: Iterable[int]
    pos: Iterable[int]
    x: int
    y: int
    def __getattr__(self, name):
        if name == 'l':
            return self.left
        elif name == 'm':
            return self.middle
        elif name == 'r':
            return self.right
        elif name == 'pos':
            return self._pos
        elif name == 'x':
            return self.pos[0]
        elif name == 'y':
            return self.pos[1]
        else:
            return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name == 'x':
            name = 'pos'
            value = (value, self._pos[1])
        if name == 'y':
            name = 'pos'
            value = (self._pos[0], value)
        if name == 'pos':
            pass # TODO: Set mouse position
        else:
            return super().__setattr__(name, value)

# Make class for controller

# events need to be done
def _upd():
    Keys._keyEvs = []

    ev = sdl2.SDL_Event()
    while sdl2.SDL_PollEvent(ev) != 0:
        if ev.type == sdl2.SDL_WINDOWEVENT and ev.window.event in (
                sdl2.SDL_WINDOWEVENT_RESIZED,
                sdl2.SDL_WINDOWEVENT_SIZE_CHANGED
            ):
            Core._resize_event(ev)
        o = _translateEv(ev)
        if o is not None:
            Keys._keyEvs.append(o)

    Keys._kbdState = sdl2.SDL_GetKeyboardState(None)
    mods = sdl2.SDL_GetModState()
    Keys.mShift = mods & sdl2.KMOD_SHIFT
    Keys.mAlt = mods & sdl2.KMOD_ALT
    Keys.mCtrl = mods & sdl2.KMOD_CTRL
    Keys.mGui = mods & sdl2.KMOD_GUI
    Keys.mNumLock = mods & sdl2.KMOD_NUM
    Keys.mCapsLock = mods & sdl2.KMOD_CAPS

    buttons = sdl2.ext.mouse_button_state()
    Mouse.left = bool(buttons.left)
    Mouse.middle = bool(buttons.middle)
    Mouse.right = bool(buttons.right)
    Mouse.x1 = bool(buttons.x1)
    Mouse.x2 = bool(buttons.x2)
    Mouse._pos = sdl2.ext.mouse_coords()

def update():
    """
    Updates interaction stuff!
    """
    _upd()
def getUpdates():
    """
    Updates interaction stuff, then yields all events that have occurred. This is a generator (use in `for ev in Ix.getUpdates()` loops).
    """
    _upd()
    yield from Keys._keyEvs
def loopEvs():
    """
    Loops over all the events collected earlier. DOES NOT POLL FOR NEW EVENTS! Only loops over events as collected from last update.

    This is a generator (use in `for ev in Ix.loopEvs()` loops)
    """
    yield from Keys._keyEvs

def flush():
    """
    Do not look at any of the events, just clear the queue and update interaction stuff.

    This means when asked for events this frame it will give an empty list.
    """
    sdl2.SDL_FlushEvents(sdl2.SDL_FIRSTEVENT, sdl2.SDL_LASTEVENT)
    _upd()

def flushNoUpdate():
    """
    Flush the events without updating the user interface class.
    This means all the user interface stuff will be left over from last time and will cause issues if not handled correctly
    
    Only useful for times where the user does nothing e.g. loading screens and you KNOW that nothing will poll for user input
    But even then, using this function is sketchy, and should be avoided.
    """
    sdl2.SDL_FlushEvents(sdl2.SDL_FIRSTEVENT, sdl2.SDL_LASTEVENT)

def handleBasic() -> bool:
    """
    Updates interaction stuff, returning False if need to quit (escape key or window close events recieved) and True otherwise

    This can be used like `while Ix.handleBasic(): ...`

    Returns:
        bool: Whether the application should quit (False) or continue running (True)
    """
    _upd()
    return not any(
            i.typ == EvTyp.Quit or
            ((kev := KeyEvent(i, EvTyp.KeyDown)) and kev.keycode == sdl2.SDLK_ESCAPE)
        for i in Keys._keyEvs
    )


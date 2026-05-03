from types import MappingProxyType
from typing import TypeVar, Self
from enum import IntEnum
import sdl2

class EvTyp(IntEnum):
    Quit = 0x0
    """When the user exits the program"""

    Keyboard = 0x1
    """A general keyboard event"""
    KeyDown = 0x11
    """The user just pressed a physical key (for text inputs please use KeyType)"""
    KeyUp = 0x21
    """The user just released a physical key"""
    KeyType = 0x31
    """The user just typed some text (this is preferred over keydown for text inputting as it allows IMEs to work)"""
    KeyTyping = 0x41
    """The user is currently typing text with their IME"""

    Mouse = 0x2
    """A general mouse event"""
    MouseClick = 0x12
    """A mouse button's press state just changed (use MouseDown or MouseUp for finer controll as needed)"""
    MouseDown = 0x112
    """A mouse button was just pressed"""
    MouseUp = 0x212
    """A mouse button was just released"""
    MouseMove = 0x22
    """The mouse was just moved"""
    MouseScroll = 0x32
    """The mouse was just scrolled"""

    FileDrop = 0x3
    """A generic file drop event"""
    FileDropStart = 0x13
    """Something is beginning to get dropped onto the window"""
    FileDropEnd   = 0x23
    """Something finished getting dropped onto the window (to handle what, use FileDropText or FileDropFile)"""
    FileDropText  = 0x33
    """Text was dropped onto the window (may have multiple events if the OS drops it in chunks)"""
    FileDropFile  = 0x43
    """A file was dropped onto the window (only one file - multiple events happen for multiple files)"""

    Controller = 0x4
    """A controller event has occurred"""
    ContrDevice = 0x14
    """A controller has been connected, disconnected or updated"""
    ContrDevConnect = 0x114
    """A controller was connected"""
    ContrDevDiscon = 0x214
    """A controller was disconnected"""
    ContrDevRemap = 0x314
    """A controller was remapped"""
    ContrAxis = 0x24
    """A controller had an axis event (e.g. from a joystick)"""
    ContrBtn = 0x34
    """A controller had a button event"""
    ContrBtnDown = 0x134
    """A controller button was pressed"""
    ContrBtnUp = 0x234
    """A controller button was released"""
    ContrSensor = 0x44
    """A controller sensor had an update"""
    # If someone wants controller touchpad events one day it's under SDL_CONTROLLERTOUCHPADDOWN, SDL_CONTROLLERTOUCHPADUP and SDL_CONTROLLERTOUCHPADMOTION

    Touch = 0x5
    """A general touch event"""
    TouchSingle = 0x15
    """A touch event with a single finger has occurred"""
    TouchMulti  = 0x25
    """A touch event with multiple fingers has occurred"""
    TouchDollar = 0x35
    """A touch event that follows a preset dollar pattern that was defined earlier has occurred"""

    Clipboard = 0x6
    """The clipboard has been changed"""

    Audio = 0x7
    """An audio device has been added or removed"""
    AudioAdded = 0x17
    """An audio device has been added"""
    AudioRemoved = 0x27
    """An audio device has been removed"""

    Sensor = 0x8
    """A sensor has had an update"""

    Window = 0x9
    """The window has had an update"""


    User = 0xF
    """Some user event has occurred"""


T = TypeVar("T")
def Dataclass(cls: T) -> T:
    annotations = getattr(cls, '__annotations__', {})
    fields = list(annotations.keys())
    for c in cls.__bases__:
        fields.extend(list(getattr(c, '__annotations__', {}).keys()))
    slots = tuple(fields)

    defaults = {}
    for name in fields:
        if hasattr(cls, name):
            defaults[name] = getattr(cls, name)

    def _dc_init(self, *args, **kwargs):
        if len(args) > len(fields):
            raise TypeError(
                f"Expected at most {len(fields)} positional arguments, got {len(args)}"
            )

        values = {}

        for name, value in kwargs.items():
            if name not in fields:
                raise TypeError(f"Got an unexpected keyword argument {name!r}")
            values[name] = value

        missing = []
        for name in fields:
            if name not in values:
                if name in defaults:
                    values[name] = defaults[name]
                else:
                    missing.append(name)

        if missing:
            missing_str = ", ".join(missing)
            raise TypeError(f"Missing required arguments: {missing_str}")

        for name in fields:
            setattr(self, name, values[name])

    def __repr__(self):
        field_strs = (f"{name}={getattr(self, name)!r}" for name in fields)
        return f"{cls.__name__}({', '.join(field_strs)})"

    new_namespace = {}
    for name, value in cls.__dict__.items():
        if name in ('__dict__', '__weakref__', '__slots__'):
            continue
        if name in fields:
            continue
        new_namespace[name] = value

    new_namespace['__slots__'] = slots
    new_namespace['_dc_init'] = _dc_init
    new_namespace['__annotations__'] = MappingProxyType(annotations)
    new_namespace['__repr__'] = __repr__

    NewCls = type(cls.__name__, cls.__bases__, new_namespace)
    return NewCls

@Dataclass
class Event:
    timestamp: int
    typ: int

    def __new__(cls, var: 'Event', typ: int = None) -> Self:
        """
        Check and type convert to an Event type

        This checks if the input `var` is of a type and returns the var if it is or False if it is not.

        If `typ` is set it checks if the type of the object is like the type specified,
        and if unset it checks against all the types this class can contain.
        `typ` must be a type that can be found in this class.

        A type that is 'like' this is e.g. if this class handled `ContrDevConnect` events, you could specify type `ContrDevice`.

        Example usage: for checking if the event `event` is an escape key with type hinting:
        ```py
        if (keyev := KeyEvent(event, EvTyp.KeyDown)) and keyev.key == 'Escape':
            ... # Can use keyev here for type hinting
        ```
        """
        if typ is None:
            if var.typ not in cls._types.values():
                return False
            return var
        if not any((k & typ)==typ for k in cls._types.values()):
            raise ValueError(
                'Input type must be avaliable in this class, but is not!'
            )
        if (var.typ & typ) != typ:
            return False
        return var

    def __init__(self, *args, **kwargs): pass

    _types = {}
    @classmethod
    def _from_sdl(this, cls, ev, typ, **kwargs):
        return cls.create(
            timestamp = ev.timestamp,
            typ = typ,
            **kwargs
        )
    @classmethod
    def create(cls, **kwargs):
        """
        Create a new event object. Not for the light-hearted.
        """
        o = object.__new__(cls)
        o._dc_init(o, **kwargs)
        return o

    def copy(self) -> Self:
        return self.create(
            **{i: getattr(self, i) for i in self.__slots__}
        )


@Dataclass
class QuitEvent(Event):
    _types = { sdl2.SDL_QUIT: EvTyp.Quit }

    @classmethod
    def _from_sdl(cls, ev, typ):
        return Event._from_sdl(cls, ev.quit, typ)

@Dataclass
class KeyEvent(Event):
    window_id: int
    """ID of the window that received the event"""

    state: bool
    """True if key is pressed, False if released"""
    repeat: bool
    """True if this event is a repeated key press"""
    @property
    def initial(self) -> bool:
        """True if this event is the first press of the key, False if it's repeating or releasing"""
        return self.state and not self.repeat

    scancode: int
    """Hardware scancode of the key"""
    keycode: int
    """Keycode of the key (abstracted from scancode)"""
    @property
    def scode(self) -> str:
        """The string name of the scancode"""
        return sdl2.SDL_GetScancodeName(self.scancode).decode()
    @property
    def key(self) -> str:
        """The string name of the key"""
        return sdl2.SDL_GetKeyName(self.keycode).decode()

    _modifiers: int
    def modifs(self, *, shift=False, ctrl=False, alt=False, gui=False) -> bool:
        """
        Find out if the specified modifiers are pressed when this key is

        Used like this: `ev.modifs(shift=1, ctrl=1)` returns if the shift and ctrl modifiers are pressed (can use True instead of 1 if desired)

        Modifiers present: `shift`, `ctrl`, `alt`, `gui` (windows/super/command key)
        """
        mask = sdl2.KMOD_SHIFT * bool(shift) + \
               sdl2.KMOD_CTRL * bool(ctrl) + \
               sdl2.KMOD_ALT * bool(alt) + \
               sdl2.KMOD_GUI * bool(gui)
        return (self._modifiers & mask) == mask

    _types = {
        sdl2.SDL_KEYDOWN: EvTyp.KeyDown,
        sdl2.SDL_KEYUP: EvTyp.KeyUp
    }
    @classmethod
    def _from_sdl(cls, ev, typ):
        ev = ev.key
        k = ev.keysym
        return Event._from_sdl(cls, ev, typ,
            window_id = ev.windowID,
            state = ev.state == sdl2.SDL_PRESSED,
            repeat = bool(ev.repeat),
            scancode = k.scancode,
            keycode = k.sym,
            _modifiers = k.mod
        )

@Dataclass
class MouseEvent(Event):
    window_id: int
    """ID of the window that received the event"""

    pos: tuple[int]
    """Mouse position (relative to window)"""
    rel: tuple[int] = (0, 0)
    """Relative motion (or scroll direction)"""

    button: int = 0
    """Mouse button (1=left, 2=middle, 3=right, etc.)"""
    state: bool = False
    """True if button pressed, False if released"""
    clicks: int = 0
    """Number of clicks (for button events)"""

    _types = {
        sdl2.SDL_MOUSEMOTION: EvTyp.MouseMove,
        sdl2.SDL_MOUSEBUTTONDOWN: EvTyp.MouseDown,
        sdl2.SDL_MOUSEBUTTONUP: EvTyp.MouseUp,
        sdl2.SDL_MOUSEWHEEL: EvTyp.MouseScroll,
    }

    def translated(self, dx, dy) -> Self:
        new = self.copy()
        new.pos = (new.pos[0]+dx, new.pos[1]+dy)
        return new

    @classmethod
    def _from_sdl(cls, ev, typ):
        if typ == EvTyp.MouseMove:
            ev = ev.motion
            return Event._from_sdl(cls, ev, typ,
                window_id = ev.windowID,
                pos = (ev.x, ev.y),
                rel = (ev.xrel, ev.yrel)
            )

        elif typ in (EvTyp.MouseDown, EvTyp.MouseUp):
            ev = ev.button
            return Event._from_sdl(cls, ev, typ,
                window_id = ev.windowID,
                pos = (ev.x, ev.y),
                button = ev.button,
                state = ev.state == sdl2.SDL_PRESSED,
                clicks = ev.clicks
            )

        elif typ == EvTyp.MouseScroll:
            ev = ev.wheel
            return Event._from_sdl(cls, ev, typ,
                window_id = ev.windowID,
                pos = (ev.mouseX, ev.mouseY),
                rel = (ev.x, ev.y)
            )


EVENT_LIST = (
    QuitEvent,
    KeyEvent,
    MouseEvent,
)
EVENT_NAMES = [
    ev.__name__ for ev in EVENT_LIST
]

_EVENT_MAP = None
def _getEvMap():
    global _EVENT_MAP
    if _EVENT_MAP is None:
        _EVENT_MAP = {}
        for evtyp in EVENT_LIST:
            _EVENT_MAP.update({
                t: (evtyp, evtyp._types[t])
                for t in evtyp._types
            })
    return _EVENT_MAP


def _translateEv(ev):
    map = _getEvMap()
    if ev.type in map:
        evtyp, typ = map[ev.type]
        return evtyp._from_sdl(ev, typ)
    return None

__all__ = [
    'EvTyp',
    'Event',
    'EVENT_LIST',
    *EVENT_NAMES,
    '_translateEv'
]


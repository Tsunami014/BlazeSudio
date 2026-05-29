import sdl2

def _mkmouse(id):
    return sdl2.mouse.SDL_CreateSystemCursor(getattr(sdl2.mouse, "SDL_SYSTEM_CURSOR_"+id))

ARROW = _mkmouse("ARROW")
IBEAM = _mkmouse("IBEAM")
TEXT = IBEAM
HAND = _mkmouse("HAND")
NO = _mkmouse("NO")
WAIT = _mkmouse("WAIT")
WAIT_ARROW = _mkmouse("WAITARROW")
CROSSHAIR = _mkmouse("CROSSHAIR")
CROSS = CROSSHAIR
SIZE_ALL = _mkmouse("SIZEALL")
"""4 pointed arrow"""
SIZE_NS = _mkmouse("SIZENS")
"""Arrow pointing up-down (north-south)"""
SIZE_WE = _mkmouse("SIZEWE")
"""Arrow pointing left-right (west-east)"""
SIZE_NESW = _mkmouse("SIZENESW")
"""Arrow pointing from the top-right to bottom-left (north-east to south-west)"""
SIZE_NWSE = _mkmouse("SIZENWSE")
"""Arrow pointing from the top-left to bottom-right (north-west to south-east)"""

hidden = False
def Hide():
    global hidden
    hidden = True
    sdl2.SDL_ShowCursor(sdl2.SDL_DISABLE)
def Show():
    global hidden
    hidden = False
    sdl2.SDL_ShowCursor(sdl2.SDL_ENABLE)

def Set(curs):
    if hidden:
        Show()
    sdl2.mouse.SDL_SetCursor(curs)
def Default():
    Set(sdl2.SDL_GetDefaultCursor())

from .base import (
    FindRadius,
    WrapJoints,
    FindBounds,
    OverConstrainedError
)
from .graphic import WrapImage

def getShapeFromInv(segs: list[tuple[int,int,int|None]], width: int):
    """
    This gets a 'shape' you can use in the wrap functions from the *inverse*!

    Basically instead of only having the straight lines being what you specify,
    this makes the entire image into a circle *except* for the straight bits you specify!

    Args:
        segs: The list of segments, in the form [startx, endx, angle|None]
        width: The width of the image being wrapped
    """
    result = []
    x = 0

    for start, end, angle in sorted(segs):
        result += [(i, None) for i in range(x, start)]
        result.append((start, angle))
        x = end

    result += [(i, None) for i in range(x, width)]
    return result

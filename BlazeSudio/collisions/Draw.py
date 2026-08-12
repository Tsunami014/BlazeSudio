from .core import checkShpType, ShpTyps, ShpGroups, Shape
from BlazeSudio.graphicsCore import base, Draw

def drawShape(shape: Shape, colour: tuple[int, int, int], width: int = 0) -> base.NormalisedOp:
    """
    Returns a draw Op for a shape

    Args:
        shape (Shape): The shape to generate the draw op for.
        colour (tuple[int, int, int]): The colour to draw the shape with.
        width (int, optional): The width of the lines to draw. Defaults to 0.
    """
    if checkShpType(shape, ShpTyps.Point):
        return Draw.Circle(shape.x, shape.y, width, 0, colour)
    elif checkShpType(shape, ShpTyps.Line):
        return Draw.Line(shape.p1, shape.p2, width, colour)
    elif checkShpType(shape, ShpTyps.Arc):
        return base.Op() # TODO - shape.x, shape.y, shape.r, shape.startAng, shape.endAng
    elif checkShpType(shape, ShpTyps.Circle):
        return Draw.Circle(shape.x, shape.y, shape.r, width, colour)
    elif checkShpType(shape, ShpGroups.CLOSED):
        return Draw.Polygon(shape.toPoints(), width, colour)
    elif checkShpType(shape, ShpGroups.GROUP):
        for i in shape.shapes:
            drawShape(i, colour, width)
    elif checkShpType(shape, ShpTyps.NoShape):
        pass
    else:
        raise ValueError(f'Cannot draw shape of type {type(shape)}')

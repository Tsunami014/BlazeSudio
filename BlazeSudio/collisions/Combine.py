from .core import (
    pointLike, BASEBOUNCINESS,
    Shape, Shapes,
    NoShape, Point, Line, Rect, Polygon,
    checkShpType, ShpTyps, ShpGroups
)
from typing import Iterable

def boundingBox(*shapes: Rect) -> Shapes:
    """
    Makes a new shape which is the bounding box of all the shapes combined.

    Returns:
        Shapes: A Shapes object containing one rectangle (if there are any shapes in shapes; else nothing) which is the bounding box around every input shape.
    """
    if not shapes:
        return Shapes()
    rs = [s.rect() for s in shapes]
    mins, maxs = [
        min(i[0] for i in rs),
        min(i[1] for i in rs)
    ], [
        max(i[2] for i in rs),
        max(i[3] for i in rs)
    ]
    return Shapes(Rect(
        *mins,
        maxs[0]-mins[0],
        maxs[1]-mins[1]
    ))

def combineRects(*shapes: Rect) -> Shapes:
    """
    Combines adjacent rectangles.
    What this means is if you have 2 rectangles exactly touching they will combine to one
    ```
    +-+-+      +---+
    | | |  ->  |   |
    +-+-+      +---+
    ```
    This will only work if the combination would exactly encompass each shape without any room for air and would be a rectangle.
    For a more general combination, try using `.to_polygons()` instead.

    Returns:
        Shapes: A Shapes object with the rectangles from the input shapes combined
    """
    if not shapes:
        return Shapes()
    shapes, others = [i for i in shapes if checkShpType(i, ShpTyps.Rect)], [i for i in shapes if not checkShpType(i, ShpTyps.Rect)]
    merged = True
    while merged:
        merged = False
        # Sort shapes by x-coordinate
        shapes = sorted(shapes, key=lambda x: x.x)
        outshapes1 = []
        
        while shapes:
            rect = shapes.pop(0)
            for i in shapes:
                if rect.y == i.y and rect.h == i.h and (rect.x + rect.w >= i.x):
                    rect.w = max(rect.x + rect.w, i.x + i.w) - rect.x
                    shapes.remove(i)
                    merged = True
                    break
            outshapes1.append(rect)
        
        # Sort shapes by y-coordinate
        outshapes1 = sorted(outshapes1, key=lambda x: x.y)
        outshapes2 = []
        
        while outshapes1:
            rect = outshapes1.pop(0)
            for i in outshapes1:
                if rect.x == i.x and rect.w == i.w and (rect.y + rect.h >= i.y):
                    rect.h = max(rect.y + rect.h, i.y + i.h) - rect.y
                    outshapes1.remove(i)
                    merged = True
                    break
            outshapes2.append(rect)
        
        shapes = outshapes2
    
    return Shapes(*shapes, *others)

def union(*shapes: Shape) -> Shapes: # FIXME
    """
    Combine all the input shapes with a unary union. Still in progress and doesn't work too well.

    Returns:
        Shapes: The union of all the shapes.
    """
    if not shapes:
        return Shapes()
    def reformat(obj):
        if checkShpType(obj, ShpGroups.CLOSED):
            return obj
        elif checkShpType(obj, ShpTyps.Line):
            return Polygon(obj.p1, obj.p2, obj.p2, obj.p1)
        # TODO: More
    reform = [reformat(s) for s in shapes]
    shapes = [reform[i] for i in range(len(reform)) if reform[i]]
    outshps = []
    while shapes:
        s = shapes.pop(0)
        colls = [i.collides(s) for i in outshps]
        if any(colls):
            for i in range(len(colls)):
                if colls[i]:
                    newpts = []
                    oshps = [s, outshps[i]]
                    lns = [j.toLines() for j in oshps]
                    direc = 1
                    check = 0
                    checked = []
                    # TODO: When objs are covered
                    ps = [any(k.collides(Point(*j)) for k in oshps if k != s) for j in s.toPoints()]
                    j = ps.index(False)
                    while True:
                        if (check, j) not in checked:
                            checked.append((check, j))
                            ln = lns[check][j]
                            p1 = ln.p1 if direc == 1 else ln.p2
                            p2 = ln.p2 if direc == 1 else ln.p1
                            newpts.append(p1)
                            wheres = []
                            for other in range(len(oshps)):
                                if other != check:
                                    if ln.collides(oshps[other]):
                                        for k in range(len(lns[other])):
                                            if ln.collides(lns[other][k]):
                                                ws = ln.whereCollides(lns[other][k])
                                                wheres.extend(zip(ws, [(other, k) for _ in range(len(ws))]))
                            if wheres != []:
                                wheres.sort(key=lambda x: (x[0][0]-p1[0])**2+(x[0][1]-p1[1])**2)
                                newpts.append(wheres[0][0])
                                # Correct direction handling
                                if oshps[check].collides(Point(*lns[wheres[0][1][0]][wheres[0][1][1]].p2)):
                                    direc = -1
                                else:
                                    direc = 1
                                check = wheres[0][1][0]
                                j = wheres[0][1][1]
                            else:
                                newpts.append(p2)
                        else:
                            break
                        j = (j + direc) % len(lns[check])
                    outshps[i] = Polygon(*newpts)
        else:
            outshps.append(s)
    return Shapes(*outshps)

def pointsToShape(*points: Iterable[pointLike], bounciness: float = BASEBOUNCINESS) -> Shape:
    """
    Converts a list of points to a shape object.
    
    No points: NoShape()
    One point: Point()
    2 points: Line()
    4 points and in the shape of a rectangle: Rect()
    Otherwise: Polygon()

    This differs from `ShapeCombiner.pointsToPoly` in that **this** will connect all the points with lines, \
*instead* of creating a polygon to envelop them all.

    Args:
        *points (pointLike): The points to convert to a shape.
        bounciness (float, optional): The bounciness of the output shape. Defaults to 0.7.

    Returns:
        Shape: The shape object made from the points
    """
    if len(points) == 0:
        return NoShape()
    elif len(points) == 1:
        return Point(*points[0], bounciness)
    if len(points) == 2:
        return Line(tuple(points[0]), tuple(points[1]), bounciness)

    if len(points) == 4:
        x_vals = {p[0] for p in points}
        y_vals = {p[1] for p in points}

        # To form a rectangle, we should have exactly two unique x-values and two unique y-values
        if len(x_vals) == 2 and len(y_vals) == 2:
            x_min, y_min = min(x_vals), min(y_vals)
            return Rect(x_min, y_min, max(x_vals)-x_min, max(y_vals)-y_min)
    
    return Polygon(*(tuple(i) for i in points), bounciness=bounciness)

def convexHull(*shapes: Iterable[Shape], bounciness: float = BASEBOUNCINESS) -> Shape:
    """
    Outputs a shape that entirely covers the outside of all the points, without any caves (a convex hull)
    """
    points = sorted({tuple(j) for s in shapes for j in s.toPoints()})
    if len(points) == 0:
        return NoShape()
    if len(points) == 1:
        return Point(*points[0], bounciness)
    if len(points) == 2:
        return Point(*points, bounciness)

    def cross(o, a, b):
        # Cross product of vectors OA and OB. Positive => counter-clockwise turn.
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    # Build lower hull
    lower = []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    # Build upper hull
    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    # Concatenate, removing the last point of each half (it's repeated at the start of the other)
    return Polygon(*lower[:-1], *upper[:-1], bounciness=bounciness)

import math
from enum import IntEnum
from typing import Union, Iterable, Any

Number = Union[int, float]
verboseOutput = Union[Iterable[Any], None]
pointLike = Iterable[Number]
AVERYSMALLNUMBER: Number = 1e-6 # This will totally not come back to haunt me later
BASEPRECISION: Number = 5
BASEBOUNCINESS: Number = 0.7 # The lower the less bouncy, 1 = reflects perfectly (but there will always be rounding imperfections, so it won't be *perfect* perfect)

__all__ = [
    'rotate',
    'rotateBy0',
    'direction',
    'pointOnCircle',

    'ShpGroups',
    'ShpTyps',
    'checkShpType',
    'ClosedShape',

    'Shape',
    'NoShape',
    'Shapes',
    'Point',
    'Line',
    'Circle',
    'Arc',
    'Rect',
    'RotatedRect',
    'Polygon',
]

def rotate(origin: pointLike, point: pointLike, angle: Number) -> pointLike:
    """
    Rotate a point clockwise by a given angle around a given origin.
    
    ### The angle should be given in **degrees**.

    Args:
        origin (pointLike): The point to rotate around
        point (pointLike): The point to rotate
        angle (Number): The angle to rotate around in degrees

    Returns:
        pointLike: The rotated point
    """
    angle = math.radians(angle)
    cos = math.cos(angle)
    sin = math.sin(angle)
    ydiff = (point[1] - origin[1])
    xdiff = (point[0] - origin[0])
    
    qx = origin[0] + cos * xdiff - sin * ydiff
    qy = origin[1] + sin * xdiff + cos * ydiff
    return qx, qy

def rotateBy0(point: pointLike, angle: Number) -> pointLike:
    """
    Rotate a point clockwise by a given angle around the origin.

    ### The angle should be given in **degrees**.

    Args:
        point (pointLike): The point to rotate
        angle (Number): The angle to rotate around in degrees

    Returns:
        pointLike: The rotated point
    """
    angle = math.radians(angle)
    cos = math.cos(angle)
    sin = math.sin(angle)
    qx = cos * point[0] - sin * point[1]
    qy = sin * point[0] + cos * point[1]
    return qx, qy

def direction(fromPoint: pointLike, toPoint: pointLike) -> Number:
    """
    Finds the direction of `toPoint` from the origin of `fromPoint`

    ### The angle returned is in **radians**.

    Args:
        fromPoint (pointLike): The origin point
        toPoint (pointLike): The point to find the direction to

    Returns:
        Number: The direction in radians OF `toPoint` FROM `fromPoint`
    """
    return math.atan2(toPoint[1]-fromPoint[1], toPoint[0]-fromPoint[0])

def pointOnCircle(angle: Number, strength: Number=1) -> pointLike:
    """
    Finds the point on the unit circle at a given angle with a given strength

    ### The angle should be given in **radians**.

    Args:
        angle (Number): The angle in radians
        strength (Number): The distance from the origin. Defaults to 1.

    Returns:
        pointLike: The point on the unit circle at angle `angle` * strength
    """
    return math.cos(angle)*strength, math.sin(angle)*strength

class ShpGroups(IntEnum):
    """
    An enum representing the different groups you can put shapes in.
    """
    CLOSED = 0
    """These shapes start in one spot and end in the same spot"""
    LINES = 1
    """Shapes that make the outer edges of other shapes"""
    NOTSTRAIGHT = 2
    """Shapes that are not straight; e.g. Circles"""
    SPLITTABLE = 3
    """Shapes that can be split into lines (e.g. Polygons)"""
    GROUP = 4
    """A group of other shapes"""

class ShpTyps(IntEnum):
    """
    An enum representing the different possible shapes.
    """
    NoShape = -1
    Group = -2
    Point = -3
    Line = -4
    Circle = -5
    Arc = -6
    Rect = -7
    RotRect = -8
    Polygon = -9

def checkShpType(shape: Union['Shape', 'Shapes'], *typs: Union[ShpTyps, ShpGroups]) -> bool:
    """
    Checks to see if a shape is of a certain type or group.

    This checks if it is of ANY of the specified types or groups.

    Args:
        shape (Shape or Shapes]): The input shape or shapes to check the type of.
        *typs (Iterable[ShpTypes | ShpGroups]): The shape type(s) &/or group(s) to check for.

    Returns:
        bool: Whether the shape is of the specified type(s) or group(s).
    """
    typ_set = set(typs)
    if typ_set.intersection(shape.GROUPS) or shape.TYPE in typ_set:
        return True
    return False


class Shape:
    """The base Shape class. This defaults to always collide.
    This class always collides; so *can* be used as an infinite plane, but why?"""
    GROUPS = set()
    TYPE = ShpTyps.NoShape
    x: Number = 0
    y: Number = 0
    bounciness: Number
    def __init__(self, bounciness: float = BASEBOUNCINESS):
        """
        Args:
            bounciness (float, optional): How bouncy this object is. 1 = rebounds perfectly, <1 = eventually will stop, >1 = will bounce more each time. Defaults to 0.7.
        """
        self.bounciness: Number = bounciness
    
    def collides(self, othershape: Union['Shape','Shapes',Iterable['Shape']]) -> bool:
        """
        Whether this shape collides with another shape(s)

        Args:
            othershape (Shape / Shapes / Iterable[Shape]): The shape(s) to check for collision with

        Returns:
            bool: whether or not this shape collides with any of the input shape(s)
        """
        if isinstance(othershape, Shape):
            return self._collides(othershape)
        for s in othershape:
            if s._collides(self):
                return True
        return False
    
    def whereCollides(self, othershape: Union['Shape','Shapes',Iterable['Shape']]) -> Iterable[pointLike]:
        """
        Finds where this shape collides with another shape(s)

        Args:
            othershape (Shape / Shapes / Iterable[Shape]): The shape(s) to check for collision with.

        Returns:
            Iterable[pointLike]: Points that lie both on this shape and the input shape(s)
        """
        if isinstance(othershape, Shape):
            return self._where(othershape)
        points = []
        for s in othershape:
            points.extend(s._where(self))
        return points
    
    def isContaining(self, othershape: Union['Shape','Shapes',Iterable['Shape']]) -> bool:
        """
        Finds whether this shape fully encloses `othershape`; if `whereCollides` returns `[]` but `collides` returns True. But (most of the time) more optimised than that.

        Args:
            othershape (Shape / Shapes / Iterable[Shape]): The shape to check if it is fully enclosed within this shape.

        Returns:
            bool: Whether the shape is fully enclosed within this shape.
        """
        if isinstance(othershape, Shape):
            return self._contains(othershape)
        for s in othershape:
            if self._contains(s):
                return True
        return False

    def distance_to(self, othershape: 'Shape') -> Number:
        """
        Finds the distance between this shape and another shape.

        Args:
            othershape (Shape): The other shape to find the distance to

        Returns:
            Number: The distance between this shape and the other shape
        """
        thisP = self.closestPointTo(othershape)
        otherP = othershape.closestPointTo(self)
        return math.hypot(thisP[0]-otherP[0], thisP[1]-otherP[1])
    
    def check_rects(self, othershape: 'Shape') -> bool:
        """
        Check whether this shape's bounding box collides with the other shape's.
        This can be used for a very fast way to know if shapes *aren't* colliding, but to find if they **are** then use `collides`.
        In fact, the `collides` method already uses this in it, so there isn't much need for you to use it.

        Args:
            othershape (Shape): _description_

        Returns:
            bool: Whether the bounding boxes of this object an the othershape collide
        """
        thisr, otherr = self.rect(), othershape.rect()
        return thisr[0] <= otherr[2] and thisr[2] >= otherr[0] and thisr[1] <= otherr[3] and thisr[3] >= otherr[1]
    
    def __repr__(self): return str(self)
    
    # Replace these
    def _collides(self, othershape: 'Shape') -> bool:
        return True
    
    def _where(self, othershape: 'Shape') -> Iterable[pointLike]:
        return []

    def _contains(self, othershape: 'Shape') -> bool:
        return True
    
    def closestPointTo(self, othershape: 'Shape', returnAll: bool = False) -> pointLike|Iterable[pointLike]:
        """
        Finds the closest point ON THIS OBJECT **TO** the other object

        Args:
            othershape (Shape): The other shape to find the closest point to
            returnAll (bool, optional): Whether to return *all* the potential closest points sorted in order of closeness or just **the** closest. Defaults to False (only the closest).

        Returns:
            pointLike|Iterable[pointLike]: The closest point(s) on this object to the other object. Whether this is an iterable or not depends on the `returnAll` parameter.
        """
        if returnAll:
            return [(0, 0)]
        return (0, 0)
    
    def isCorner(self, point: pointLike, precision: Number = BASEPRECISION) -> bool:
        """
        Finds whether a point is on a corner of this shape.

        Args:
            point (pointLike): The point to find if it's a corner
            precision (Number, optional): The decimal places to round to to check. Defaults to 5.

        Returns:
            bool: Whether the point is on a corner of this shape
        """
        return True
    
    def tangent(self, point: pointLike, vel: pointLike) -> Number:
        """
        Finds the tangent on this surface to a point with a given velocity

        Args:
            point (pointLike): The point to find the tangent of this surface from
            vel (pointLike): Which direction the point is moving (useful for example with lines for finding which side of the line the tangent should be of)

        Returns:
            Number: The tangent of this object at the point. You can -90 to get the normal.
        """
        return math.degrees(math.atan2(vel[1], vel[0])) % 360
    
    def toLines(self) -> Iterable['Line']:
        """
        Returns:
            Iterable[Line]: Get a list of all the Lines that make up this object. For anything under a ClosedShape, this will most likely be empty.
        """
        return []
    
    def toPoints(self) -> Iterable[pointLike]:
        """
        Returns:
            Iterable[pointLike]: Get a list of all the Points that make up this object. For a few shapes (e.g. circles), this will be empty.
        """
        return []
    
    def area(self) -> Number:
        """
        Gets the area of the shape.

        Returns:
            Number: The area of the shape
        """
        return float('inf')
    
    def rect(self) -> Iterable[Number]:
        """
        Returns the rectangle bounding box surrounding this object.

        Returns:
            Iterable[Number]: (min x, min y, max x, max y)
        """
        return -float('inf'), -float('inf'), float('inf'), float('inf')
    
    def handleCollisionsPos(self, oldP: 'Shape', newP: 'Shape', objs: Union['Shapes',Iterable['Shape']], vel: pointLike = [0,0], verbose: bool = False) -> tuple['Shape', pointLike, verboseOutput]:
        """
        This is called to modify objects' positions to bounce off objects.
        """
        if verbose:
            return newP, vel, []
        return newP, vel
    
    def handleCollisionsVel(self, vel: pointLike, objs: Union['Shapes',Iterable['Shape']], verbose: bool = False) -> tuple['Shape', pointLike, verboseOutput]:
        """
        This is a wrapper for `handleCollisionsPos` to handle velocity instead of position.
        """
        if verbose:
            return self, vel, []
        return self, vel
    
    def copy(self) -> 'Shape':
        """
        Copy this shape to return another with the same properties
        """
        return Shape(self.bounciness)
    
    def __getitem__(self, it: int) -> None:
        return 0

    def __setitem__(self, it: int, new: Number) -> None:
        pass

    def __iter__(self):
        return iter([])
    
    def __str__(self):
        return '<Shape>'

class NoShape(Shape):
    """A class to represent no shape. This is useful for when you want to have a shape that doesn't collide with anything."""
    def __init__(self):
        super().__init__(0)
    
    def _collides(self, othershape: Shape) -> bool:
        return False
    
    def _where(self, othershape: Shape) -> Iterable[pointLike]:
        return []
    
    def _contains(self, othershape: 'Shape') -> bool:
        return False
    
    def area(self) -> Number:
        """
        Gets the area of the shape; 0.

        Returns:
            Number: The area of the shape
        """
        return 0
    
    def copy(self) -> 'NoShape':
        """Make a copy of this non-existant shape"""
        return NoShape()
    
    def __str__(self):
        return '<NoShape>'

class Shapes:
    """A class which holds multiple shapes and can be used to do things with all of them at once."""
    GROUPS = {ShpGroups.GROUP}
    TYPE = ShpTyps.Group
    def __init__(self, *shapes: Shape, bounciness: float = BASEBOUNCINESS):
        """
        Args:
            *shapes (Shape): The shapes to start off with in this object.
            bounciness (float, optional): How bouncy this object is. 1 = rebounds perfectly, <1 = eventually will stop, >1 = will bounce more each time. Defaults to 0.7.
        
        Example:
        `Shapes(Shape1, Shape2)` OR `Shapes(*[Shape1, Shape2])`
        """
        self.bounciness = bounciness
        self.shapes = list(shapes)
    
    def add_shape(self, shape: Shape) -> None:
        """
        Adds a shape to this Shapes object.

        Args:
            shape (Shape): The desired shape to add.
        """
        self.shapes.append(shape)
    
    def add_shapes(self, *shapes: Shape) -> None:
        """
        Adds multiple shapes to this object.

        Args:
            *shapes (Shape): The shapes to add to this object.
        
        Example:
        `shapes.add_shapes(Shape1, Shape2)` OR `shapes.add_shapes(*[Shape1, Shape2])`
        """
        self.shapes.extend(list(shapes))
    
    def remove_shape(self, shape: Shape) -> None:
        """
        Removes a specific shape from this object.

        Args:
            shape (Shape): The shape to remove.
        """
        self.shapes.remove(shape)
    
    def remove_shapes(self, *shapes: Shape) -> None:
        """
        Removes multiple shapes from this object.

        Args:
            *shapes (Shape): The shapes to remove.
        
        Example:
        `shapes.remove_shapes(Shape1, Shape2)` OR `shapes.remove_shapes(*[Shape1, Shape2])`
        """
        for s in shapes:
            self.shapes.remove(s)
    
    def collides(self, shapes: Union[Shape,'Shapes',Iterable[Shape]]) -> bool:
        """
        Checks for collisions between all the shapes in this object and the input shape(s).

        Args:
            shapes (Shape / Shapes / Iterable[Shape]]): The shape(s) to check for collisions against

        Returns:
            bool: True if *any* of the shapes in this object collide with *any* of the input shapes
        """
        for s in self.shapes:
            if s.collides(shapes):
                return True
        return False

    def whereCollides(self, shapes: Union[Shape,'Shapes',Iterable[Shape]]) -> Iterable[pointLike]:
        """
        Find the points where this object collides with the input shape(s).

        Args:
            shapes (Shape / Shapes / Iterable[Shape]]): _description_

        Returns:
            Iterable[pointLike]: _description_
        """
        points = []
        for s in self.shapes:
            points.extend(s.whereCollides(shapes))
        return points
    
    def closestPointTo(self, othershape: Shape, returnAll: bool = False) -> Iterable[pointLike]:
        """
        Finds the closest point ON ANY of these objects TO the input shape.

        Args:
            othershape (Shape): The shape to find the closest points towards
            returnAll (bool, optional): Whether to return EVERY possible option, sorted from closest to furthest. Defaults to False.

        Returns:
            Iterable[pointLike]: All the closest point(s) ON each of these objects
        """
        if returnAll:
            points = []
            for s in self.shapes:
                points.extend(s.closestPointTo(othershape, True))
            def sortFunc(p):
                op = othershape.closestPointTo(Point(*p), False)
                return math.hypot(p[0]-op[0], p[1]-op[1])
            return sorted(points, key=sortFunc)
        else:
            point = None
            d = None
            for s in self.shapes:
                np = s.closestPointTo(othershape, False)
                op = othershape.closestPointTo(Point(*np), False)
                nd = math.hypot(np[0]-op[0], np[1]-op[1])
                if d is None or nd < d:
                    d = nd
                    point = np
            return point

    def isContaining(self, othershape: Union[Shape,'Shapes',Iterable[Shape]]) -> bool:
        """
        Finds whether this shape fully encloses `othershape`; if `whereCollides` returns `[]` but `collides` returns True. But more optimised than that.

        Args:
            othershape (Shape / Shapes / Iterable[Shape]): The shape to check if it is fully enclosed within this shape.

        Returns:
            bool: Whether the shape is fully enclosed within this shape.
        """
        for s in self.shapes:
            if s.isContaining(othershape):
                return True
        return False

    def isCorner(self, point: pointLike, precision: Number = BASEPRECISION) -> bool:
        """
        Finds if the point is a corner on any of the objects.

        Args:
            point (pointLike): The point to find if it's on the corner or not
            precision (Number, optional): The decimal places to round to to check. Defaults to 5.

        Returns:
            bool: Whether the point is on a corner of any of the objects.
        """
        for s in self.shapes:
            if s.isCorner(point, precision):
                return True
        return False
    
    def tangent(self, point: pointLike, vel: pointLike) -> Iterable[Number]: # TODO: Make it return just one number
        """
        Finds the tangent on each of these objects for the specified point. -90 = normal.

        Args:
            point (pointLike): The point to find the tangent from.
            vel (pointLike): Which direction the point is moving (useful for example with lines for finding which side of the line the tangent should be of)

        Returns:
            Iterable[Number]: A list of all the tangents to the specified point.
        """
        points = []
        for s in self.shapes:
            points.append(s.tangent(point, vel))
        return points
    
    # TODO: handleCollisions

    def toPoints(self) -> Iterable[pointLike]:
        """
        Returns:
            Iterable[pointLike]: Get a list of all the Points that make up this object. For a few shapes (e.g. circles), this will be empty.
        """
        points = []
        for s in self.shapes:
            points.extend(s.toPoints())
        return points
    
    def toLines(self) -> Iterable['Line']:
        """
        Returns:
            Iterable[Line]: Get a list of all the Lines that make up this object. For anything under a ClosedShape, this will most likely be empty.
        """
        lines = []
        for s in self.shapes:
            lines.extend(s.toLines())
        return lines

    def area(self) -> Number:
        """
        Gets the combined area of all the shapes.

        Returns:
            Number: The sum of all the areas of the shapes.
        """
        return sum(s.area() for s in self.shapes)

    def rect(self) -> Iterable[Number]:
        """
        Returns the rectangle bounding box surrounding every one of these objects.

        Returns:
            Iterable[Number]: (min x, min y, max x, max y)
        """
        rs = [s.rect() for s in self.shapes]
        return min(i[0] for i in rs), min(i[1] for i in rs), max(i[2] for i in rs), max(i[3] for i in rs)
    
    def copy(self) -> 'Shapes':
        """
        Make a copy of this class with a copy of each shape in it.
        """
        return Shapes(s.copy() for s in self.shapes)
    
    def copy_leave_shapes(self) -> 'Shapes':
        """
        Makes a copy of this class but keeps the same shapes.
        """
        return Shapes(*self.shapes)
    
    def __iter__(self):
        return iter(self.shapes)
    
    def __len__(self):
        return len(self.shapes)
    
    def __getitem__(self, index: int) -> Union[Shape,'Shapes']:
        return self.shapes[index]
    
    def __setitem__(self, index: int, new: Union[Shape,'Shapes']) -> None:
        self.shapes[index] = new
    
    def __repr__(self): return str(self)
    
    def __str__(self):
        shpTyps = str([i.__class__.__name__ for i in self.shapes]).replace("'", "")
        return f'<Shapes with shapes: {shpTyps}>'

# The below are in order of collision:
# Each defines how it collides if it hits anything below it, and calls the other object for collisions above.
# Also each is kinda in order of complexity.

class Point(Shape):
    TYPE = ShpTyps.Point
    """An infintesimally small point in space defined by an x and y coordinate."""
    def __init__(self, x: Number, y: Number, bounciness: float = BASEBOUNCINESS):
        """
        Args:
            x (Number): The x ordinate of this object.
            y (Number): The y ordinate of this object.
            bounciness (float, optional): How bouncy this object is. 1 = rebounds perfectly, <1 = eventually will stop, >1 = will bounce more each time. Defaults to 0.7.
        """
        super().__init__(bounciness)
        self.x, self.y = x, y
    
    def rect(self) -> Iterable[Number]:
        """
        Returns the rectangle bounding box surrounding this point.

        Returns:
            Iterable[Number]: (min x, min y, max x, max y)
        """
        return self.x, self.y, self.x, self.y
    
    def area(self) -> Number:
        """
        Gets the area of the shape; 0.

        Returns:
            Number: The area of the shape
        """
        return 0.0
    
    def toPoints(self) -> Iterable[pointLike]:
        """
        Returns:
            Iterable[pointLike]: Get a list of all the Points that make up this object; i.e. just this one point.
        """
        return [self]
    
    def _collides(self, othershape: Shape) -> bool:
        if checkShpType(othershape, ShpTyps.Point):
            return self.x == othershape.x and self.y == othershape.y
        return othershape._collides(self)
    
    def _where(self, othershape: Shape) -> Iterable[pointLike]:
        if checkShpType(othershape, ShpTyps.Point):
            return [[self.x, self.y]] if (self.x == othershape.x and self.y == othershape.y) else []
        return othershape._where(self)
    
    def closestPointTo(self, othershape: Shape, returnAll: bool = False) -> Union[pointLike, Iterable[pointLike]]:
        """
        Finds the closest point ON this object TO the other shape

        Args:
            othershape (Shape): The other shape to find the closest point towards
            returnAll (bool, optional): Whether to return ALL the possible options in order of closeness (True) or just the closest (False). Defaults to False.

        Returns:
            pointLike / Iterable[pointLike]: The closest points ON this object TO the other object
        """
        if returnAll:
            return [(self.x, self.y)]
        return (self.x, self.y)
    
    def getTuple(self) -> tuple[Number]:
        """
        Gets this object in a tuple format: (x, y).
        Do you get the point?
        """
        return (self.x, self.y)
    
    def _contains(self, othershape: Shape) -> bool:
        return False
    
    def handleCollisionsPos(self, 
                            oldPoint: Union['Point',pointLike], 
                            newPoint: Union['Point', pointLike], 
                            objs: Union[Shapes, Iterable[Shape]], 
                            vel: pointLike = [0,0], 
                            replaceSelf: bool = True, 
                            precision: Number = BASEPRECISION, 
                            verbose: bool = False
                           ) -> tuple[pointLike, pointLike, verboseOutput]:
        """
        Handles movement of this point and it bouncing off of other objects.
        It is recommended you use `.handleCollisionsVel` instead of this, as it handles velocity instead of raw movement and is easier to use.

        But if you are to use this, remember to still provide the vel param. It will sometimes provide weird results if you don't.
        It could even just be the difference in positions, it just needs to be something realistic.

        Args:
            oldPoint (Point / pointLike): The old position of this object.
            newPoint (Point / pointLike): The new position of this object.
            objs (Shapes / Iterable[Shape]): The objects this will bounce off.
            vel (pointLike, optional): The velocity that this object is going. Defaults to [0, 0].
            replaceSelf (bool, optional): Whether to replace self.x and self.y with the new position of the object after bouncing or not. Defaults to True.
            precision (Number, optional): The decimal places to round to to check (for things like corner checking). Defaults to 5.
            verbose (bool, optional): Whether to give verbose output or not. Defaults to False.

        Returns:
            tuple[pointLike, pointLike, veboseOutput?]: The new position and vel of this object respectively, and if verbose then the verboseOutput.
        
        VerboseOutput:
            DidReflect (bool): Whether the line reflected off of something
        """
        mvement = Line(oldPoint, newPoint)
        if not mvement.collides(objs):
            if verbose:
                return newPoint, vel, [False]
            return newPoint, vel
        points = []
        for o in objs:
            cs = o.whereCollides(mvement)
            points.extend(list(zip(cs, [o for _ in range(len(cs))])))
        # Don't let you move when you're in a wall
        if points == []:
            if verbose:
                return oldPoint, [0, 0], [True]
            return oldPoint, [0, 0]
        points.sort(key=lambda x: abs(x[0][0]-oldPoint[0])**2+abs(x[0][1]-oldPoint[1])**2)
        closestP = points[0][0]
        closestObj = points[0][1]
        t = closestObj.tangent(closestP, vel)
        normal = t-90
        dist_left = math.hypot(newPoint[0]-closestP[0], newPoint[1]-closestP[1]) * closestObj.bounciness
        x, y = oldPoint[0] - closestP[0], oldPoint[1] - closestP[1]
        phi = math.degrees(math.atan2(y, x))+90 # Because we have to -90 due to issues and then +180 so it becomes +90
        diff = (phi-normal) % 360
        if diff > 180:
            diff = diff - 360
        pos = rotate(closestP, [closestP[0], closestP[1]+dist_left], phi-180-diff*2)
        vel = list(rotateBy0(vel, 180-diff*2))
        vel = [vel[0]*closestObj.bounciness, vel[1]*closestObj.bounciness]
        # HACK
        smallness = rotateBy0([0,AVERYSMALLNUMBER], phi-180-diff*2)
        out, outvel = self.handleCollisionsPos((closestP[0]+smallness[0], closestP[1]+smallness[1]), pos, objs, vel, False, precision)
        if replaceSelf:
            self.x, self.y = out[0], out[1]
        if verbose:
            return out, outvel, [True]
        return out, outvel

    def handleCollisionsVel(self, 
                              vel: pointLike, 
                              objs: Union[Shapes,Iterable[Shape]], 
                              replaceSelf: bool = True, 
                              precision: Number = BASEPRECISION, 
                              verbose: bool = False
                             ) -> tuple[pointLike, pointLike, verboseOutput]:
        """
        Handles movement of this point via velocity and it bouncing off of other objects.

        Args:
            vel (pointLike): The velocity of this point
            objs (Shapes / Iterable[Shape]): The objects to bounce off of
            replaceSelf (bool, optional): Whether or not to replace self.x and self.y with the new position. Defaults to True.
            precision (Number, optional): The decimal places to round to to check (for things like corner checking). Defaults to 5.
            verbose (bool, optional): Whether to give verbose output or not. Defaults to False.

        Returns:
            tuple[pointLike, pointLike, veboseOutput?]: The new position and vel of this object respectively, and if verbose then the verboseOutput.
        
        VerboseOutput:
            DidReflect (bool): Whether the line reflected off of something
        """
        o = self.handleCollisionsPos(self, (self.x+vel[0], self.y+vel[1]), objs, vel, False, precision, verbose)
        if replaceSelf:
            self.x, self.y = o[0]
        if verbose:
            return o[0], o[1], o[2]
        return o[0], o[1]

    def copy(self) -> 'Point':
        """
        Make a brand new Point with the same values!
        """
        return Point(self.x, self.y, self.bounciness)

    def __getitem__(self, item: int) -> Number:
        if item == 0:
            return self.x
        elif item == 1:
            return self.y
        else:
            raise IndexError(
                'List index out of range! Must be 0-1, found: '+str(item)
            )
    
    def __setitem__(self, item: int, new: Number) -> None:
        if item == 0:
            self.x = new
        elif item == 1:
            self.y = new
        else:
            raise IndexError(
                'List index out of range! Must be 0-1, found: '+str(item)
            )

    def __iter__(self):
        yield self.x
        yield self.y
    
    def __str__(self):
        return f'<Point @ ({self.x}, {self.y})>'

class Line(Shape):
    """A line segment object defined by a start and an end point."""
    GROUPS = {ShpGroups.LINES}
    TYPE = ShpTyps.Line
    def __init__(self, p1: pointLike, p2: pointLike, bounciness: float = BASEBOUNCINESS):
        """
        Args:
            p1 (pointLike): The start point of this line
            p2 (pointLike): The end point of this line
            bounciness (float, optional): How bouncy this object is. 1 = rebounds perfectly, <1 = eventually will stop, >1 = will bounce more each time. Defaults to 0.7.
        """
        super().__init__(bounciness)
        self.p1, self.p2 = p1, p2
    
    def area(self) -> Number:
        """
        Gets the area of the shape; the distance between the 2 points making up the line.

        Returns:
            Number: The distance between the 2 points.
        """
        return math.hypot(self.p1[0]-self.p2[0], self.p1[1]-self.p2[1])
    
    @property
    def x(self):
        """One of the line's points' x value. Changing this will move the other point by the difference!"""
        return self.p1[0]
    @x.setter
    def x(self, value):
        diff = value - self.p1[0]
        self.p1 = [value, self.p1[1]]
        self.p2 = [self.p2[0]+diff, self.p2[1]]
    
    @property
    def y(self):
        """One of the line's points' y value. Changing this will move the other point by the difference!"""
        return self.p1[1]
    @y.setter
    def y(self, value):
        diff = value - self.p1[1]
        self.p1 = [self.p1[0], value]
        self.p2 = [self.p2[0], self.p2[1]+diff]
    
    # Some code yoinked off of https://www.geeksforgeeks.org/check-if-two-given-line-segments-intersect/ modified for this use case and debugged
    
    @staticmethod
    def _onSegment(p, a, b):
        """
        Given three collinear points p, a, b, the function checks if point p lies on line segment 'ab'
        """
        # Calculate the cross product
        cross_product = (p[1] - a[1]) * (b[0] - a[0]) - (p[0] - a[0]) * (b[1] - a[1])
        
        # If the cross product is not zero, the point is not on the line
        if abs(cross_product) != 0:
            return False
        
        # Check if the point is within the bounding box of the line segment
        return min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])
    
    def rect(self) -> Iterable[Number]:
        """
        Returns the rectangle bounding box surrounding this line.

        Returns:
            Iterable[Number]: (min x, min y, max x, max y)
        """
        return min(self.p1[0], self.p2[0]), min(self.p1[1], self.p2[1]), max(self.p1[0], self.p2[0]), max(self.p1[1], self.p2[1])
    
    def toLines(self) -> Iterable['Line']:
        """
        Returns:
            Iterable[Line]: Get a list of all the Lines that make up this object; i.e. just this one line.
        """
        return [self]
    
    def toPoints(self) -> Iterable[pointLike]:
        """
        Returns:
            Iterable[pointLike]: Get a list of all the Points that make up this object.
        """
        return [self.p1, self.p2]

    def _contains(self, othershape: Shape) -> bool:
        return False
    
    def _collides(self, othershape: Shape) -> bool:
        if checkShpType(othershape, ShpTyps.Point):
            return self.check_rects(othershape) and self._onSegment([othershape.x, othershape.y], self.p1, self.p2)
        if checkShpType(othershape, ShpTyps.Line):
            if not self.check_rects(othershape):
                return False
            # Calculate the direction of the lines
            def direction(xi, yi, xj, yj, xk, yk):
                return (xk - xi) * (yj - yi) - (yk - yi) * (xj - xi)
            
            d1 = direction(othershape.p1[0], othershape.p1[1], othershape.p2[0], othershape.p2[1], self.p1[0], self.p1[1])
            d2 = direction(othershape.p1[0], othershape.p1[1], othershape.p2[0], othershape.p2[1], self.p2[0], self.p2[1])
            d3 = direction(self.p1[0], self.p1[1], self.p2[0], self.p2[1], othershape.p1[0], othershape.p1[1])
            d4 = direction(self.p1[0], self.p1[1], self.p2[0], self.p2[1], othershape.p2[0], othershape.p2[1])
            
            # Check if the line segments straddle each other
            if d1 * d2 < 0 and d3 * d4 < 0:
                return True
            
            # Check if the points are collinear and on the segments
            return (d1 == 0 and self._onSegment((self.p1[0], self.p1[1]), (othershape.p1[0], othershape.p1[1]), (othershape.p2[0], othershape.p2[1]))) or \
                   (d2 == 0 and self._onSegment((self.p2[0], self.p2[1]), (othershape.p1[0], othershape.p1[1]), (othershape.p2[0], othershape.p2[1]))) or \
                   (d3 == 0 and self._onSegment((othershape.p1[0], othershape.p1[1]), (self.p1[0], self.p1[1]), (self.p2[0], self.p2[1]))) or \
                   (d4 == 0 and self._onSegment((othershape.p2[0], othershape.p2[1]), (self.p1[0], self.p1[1]), (self.p2[0], self.p2[1])))
        
        return othershape._collides(self)
    
    def _where(self, othershape: Shape) -> Iterable[pointLike]:
        if checkShpType(othershape, ShpTyps.Point):
            return [[othershape.x, othershape.y]] if self.collides(othershape) else []
        if checkShpType(othershape, ShpTyps.Line):
            if not self.collides(othershape):
                return []
            # This finds where the lines are colliding if they are infinite, which is why we check if they collide first
            def line(p1, p2):
                A = (p1[1] - p2[1])
                B = (p2[0] - p1[0])
                C = (p1[0]*p2[1] - p2[0]*p1[1])
                return A, B, -C
            L1, L2 = line(self.p1, self.p2), line(othershape.p1, othershape.p2)
            D  = L1[0] * L2[1] - L1[1] * L2[0]
            Dx = L1[2] * L2[1] - L1[1] * L2[2]
            Dy = L1[0] * L2[2] - L1[2] * L2[0]
            if D != 0:
                x = Dx / D
                y = Dy / D
                return [[float(x),float(y)]]
            else:
                return []
        return othershape._where(self)
    
    def closestPointTo(self, othershape: Shape, returnAll: bool = False) -> pointLike|Iterable[pointLike]:
        """
        Find the closest point ON this object TO another object.

        Args:
            othershape (Shape): The other shape to find the closest point towards.
            returnAll (bool, optional): Whether to return ALL the possible options in order of closeness (True) or just the closest (False). Defaults to False.

        Returns:
            pointLike / Iterable[pointLike]: The closest points ON this object TO the other object
        """
        if checkShpType(othershape, ShpTyps.Point):
            dx, dy = self.p2[0] - self.p1[0], self.p2[1] - self.p1[1]
            det = dx * dx + dy * dy
            if det == 0:
                return self.p1
            a = (dy * (othershape[1] - self.p1[1]) + dx * (othershape[0] - self.p1[0])) / det
            a = min(1, max(0, a))
            p = (self.p1[0] + a * dx, self.p1[1] + a * dy)
            if returnAll:
                return [p]
            return p
        elif checkShpType(othershape, ShpTyps.Line):
            colls = self.whereCollides(othershape)
            if colls != []:
                if returnAll:
                    return colls
                return colls[0]
            def calculate(ln, point, recalculate):
                p2 = ln.closestPointTo(Point(*point))
                olineP = point
                if recalculate:
                    olineP = p2
                    p2 = self.closestPointTo(Point(*p2))
                return p2, abs(p2[0]-olineP[0])**2+abs(p2[1]-olineP[1])**2
            tries = [
                calculate(self, othershape.p1, False),
                calculate(self, othershape.p2, False),
                calculate(othershape, self.p1, True),
                calculate(othershape, self.p2, True),
            ]
            tries.sort(key=lambda x: x[1])
            if returnAll:
                return [i[0] for i in tries]
            return tries[0][0]
        elif checkShpType(othershape, ShpTyps.Circle):
            return self.closestPointTo(Point(othershape.x, othershape.y), returnAll)
        elif checkShpType(othershape, ShpTyps.Arc):
            return self.closestPointTo(Point(*othershape.closestPointTo(self)))
        else: # Rects, Rotated rects and polygons
            colls = self.whereCollides(othershape)
            if colls != []:
                if returnAll:
                    return colls
                return colls[0]
            def calculate(ln, point, recalculate):
                p2 = ln.closestPointTo(Point(*point))
                olineP = point
                if recalculate:
                    olineP = p2
                    p2 = self.closestPointTo(Point(*p2))
                return p2, abs(p2[0]-olineP[0])**2+abs(p2[1]-olineP[1])**2
            tries = [
                calculate(self, p, False) for p in othershape.toPoints()
            ] + [
                calculate(ln, self.p1, True) for ln in othershape.toLines()
            ] + [
                calculate(ln, self.p2, True) for ln in othershape.toLines()
            ]
            tries.sort(key=lambda x: x[1])
            if returnAll:
                return [i[0] for i in tries]
            return tries[0][0]
    
    def isCorner(self, point: pointLike, precision: Number = BASEPRECISION) -> bool:
        """
        Finds whether a point is on a corner of this shape.

        Args:
            point (pointLike): The point to find if it's a corner
            precision (Number, optional): The decimal places to round to to check. Defaults to 5.

        Returns:
            bool: Whether the point is on a corner of this shape
        """
        def rountTuple(x):
            return (round(x[0], precision), round(x[1], precision))
        return rountTuple(self.p1) == rountTuple(point) or rountTuple(self.p2) == rountTuple(point)
    
    def tangent(self, point: pointLike, vel: pointLike) -> Number:
        """
        Finds the tangent on this surface to a point with a given velocity.

        Args:
            point (pointLike): The point to find the tangent of this surface from.
            vel (pointLike): Which direction the point is moving. In this case (for lines) it is actually very important, so please don't forget it.

        Returns:
            Number: The tangent of the line at the point. You can -90 to get the normal.
        """
        if point == self.p1:
            return math.degrees(math.atan2(self.p2[1] - self.p1[1], self.p2[0] - self.p1[0]))
        elif point == self.p2:
            return math.degrees(math.atan2(self.p1[1] - self.p2[1], self.p1[0] - self.p2[0]))
        def fixangle(angle):
            angle = angle % 360
            if angle > 180:
                angle = angle - 360
            return abs(angle) # Because we don't need to use this for anything else
        toDeg = (math.degrees(math.atan2(vel[1], vel[0]))-180) % 360
        phi = (math.degrees(math.atan2(self.p2[1] - self.p1[1], self.p2[0] - self.p1[0]))-90)
        tries = [fixangle(phi-toDeg), fixangle(phi-toDeg-180)]
        return [(phi-180)%360, phi % 360][tries.index(min(tries))]
    
    def handleCollisionsPos(self, 
                            oldLine: 'Line', 
                            newLine: 'Line', 
                            objs: Union[Shapes, Iterable[Shape]], 
                            vel: pointLike = [0, 0], 
                            replaceSelf: bool = True, 
                            precision: Number = BASEPRECISION, 
                            verbose: bool = False
                           ) -> tuple['Line', pointLike, verboseOutput]:
        """
        Handles movement of this line and it bouncing off of other objects.
        It is recommended you use `.handleCollisionsVel` instead of this, as it handles velocity instead of raw movement and is easier to use.

        But if you are to use this, remember to still provide the vel param. It will provide VERY weird results if you don't.
        It could even just be the difference in positions, it just needs to be something realistic.

        Args:
            oldLine (Line): The old Line object.
            newLine (Line): The new Line object. Should be the exact same as the old one except with the 2 points offset by the same amount.
            objs (Shapes / Iterable[Shape]): The objects this will bounce off.
            vel (pointLike, optional): The velocity that this object is going. Defaults to [0, 0].
            replaceSelf (bool, optional): Whether to move this Line to the new position after bouncing or not. Defaults to True.
            precision (Number, optional): The decimal places to round to to check (for things like corner checking). Defaults to 5.
            verbose (bool, optional): Whether to give verbose output or not. Defaults to False.

        Returns:
            tuple[Line, pointLike, veboseOutput?]: The new Line object and vel of this object respectively, and if verbose then the verboseOutput.
        
        VerboseOutput:
            CollisionType (list[int, ...] / None): The type of collision that occured for each sub-collision (if it ever collided, that is)
            DidReflect (bool): Whether the line reflected off of something
        """
        oldLine = Line(*sorted([oldLine.p1, oldLine.p2], key=lambda x: x[0]))
        newLine = Line(*sorted([newLine.p1, newLine.p2], key=lambda x: x[0]))
        mvement = Polygon(oldLine.p1, oldLine.p2, newLine.p2, newLine.p1)
        # Don't let you move when you're in a wall
        if oldLine.collides(objs):
            if verbose:
                return oldLine, [0, 0], [None, True]
            return oldLine, [0, 0]
        points = []
        hit = False
        for o in objs:
            if o.collides(mvement):
                hit = True
                ps = o.whereCollides(mvement) + [i for i in o.closestPointTo(oldLine, True) if mvement.collides(Point(*i))]
                for p in ps:
                    # The rotation is making sure the line crosses the oldLine
                    cPoint = oldLine.closestPointTo(Line(p, (p[0]-vel[0],p[1]-vel[1])))
                    points.append([p, o, cPoint, abs(p[0]-cPoint[0])**2+abs(p[1]-cPoint[1])**2])
                    #points.extend(list(zip(cs, [o for _ in range(len(cs))])))
        if not hit:
            if verbose:
                return newLine, vel, [None, False]
            return newLine, vel
        points.sort(key=lambda x: x[3])
        closestP = points[0][0] # Closest point on the OTHER object
        cPoint = points[0][2] # closestP projected onto the oldLine
        closestObj = points[0][1]
        newPoint = newLine.closestPointTo(Line(closestP, (closestP[0]+vel[0],closestP[1]+vel[1]))) # closestP projected onto the newLine

        thisNormal = math.degrees(math.atan2(oldLine[0][1]-oldLine[1][1], oldLine[0][0]-oldLine[1][0]))
        paralell = False
        thisIsOnP = oldLine.isCorner(cPoint, precision)
        if checkShpType(closestObj, ShpGroups.NOTSTRAIGHT):
            paralell = not thisIsOnP
        if not paralell:
            cLine = None
            if checkShpType(closestObj, ShpTyps.Line):
                cLine = closestObj
            elif checkShpType(closestObj, ShpGroups.CLOSED):
                colllidingLns = [i for i in closestObj.toLines() if i.collides(Point(*closestP))]
                if colllidingLns != []:
                    cLine = colllidingLns[0]
            elif checkShpType(closestObj, ShpTyps.Circle) and (not thisIsOnP):
                paralell = True
            if cLine is not None:
                sortedOtherLn = Line(*sorted([cLine.p1, cLine.p2], key=lambda x: x[0]))
                otherLnNormal = math.degrees(math.atan2(sortedOtherLn[0][1]-sortedOtherLn[1][1], sortedOtherLn[0][0]-sortedOtherLn[1][0]))
                paralell = abs(otherLnNormal%360 - thisNormal%360) < precision or abs((otherLnNormal-180)%360 - thisNormal%360) < precision
        velDiff = 180
        if paralell: # Line off line
            collTyp = 3
            # Reflect off the object's normal to the point (but really could be either point; the tangents *should* be the same)
            normal = thisNormal
            phi = math.degrees(math.atan2(newPoint[1] - closestP[1], newPoint[0] - closestP[0]))-90
        else:
            otherIsOnP = closestObj.isCorner(closestP, precision)
            if thisIsOnP and otherIsOnP: # Point off point collision
                collTyp = 0
                # Reflect off the same way as you came in (as if you can land an infintesimally small point on another infintesimally small point anyway)
                normal, phi = 0, 0
            elif thisIsOnP and (not otherIsOnP): # Point off line
                collTyp = 1
                # Reflect off the other object's normal to the point
                normal = closestObj.tangent(closestP, vel)-90
                phi = math.degrees(math.atan2(newPoint[1] - closestP[1], newPoint[0] - closestP[0]))-90 # The angle of incidence
            elif (not thisIsOnP) and otherIsOnP: # Line off point
                collTyp = 2
                # Reflect off this line's normal
                normal = thisNormal-90 # The normal off the line
                phi = math.degrees(math.atan2(closestP[1] - newPoint[1], closestP[0] - newPoint[0]))-90 # The angle of incidence
                velDiff = 0
            else:
                #raise TypeError(
                #    'Cannot have a line reflecting off of another line when they aren\'t paralell; something bad must have occured!'
                #)
                collTyp = None
                normal, phi = 0, 0
        
        if round(newPoint[0], precision) == round(closestP[0], precision) and round(newPoint[1], precision) == round(closestP[1], precision):
            phi = normal+180

        # the distance between the closest point on the other object and the corresponding point on the newLine
        dist_left = math.hypot(newPoint[0]-closestP[0], newPoint[1]-closestP[1]) * closestObj.bounciness
        diff = (phi-normal) % 360 # The difference between the angle of incidence and the normal
        if diff > 180: # Do we even need this?
            diff -= 360
        pos = rotate(closestP, [closestP[0], closestP[1] + dist_left], phi-180-diff*2)
        vel = list(rotateBy0(vel, velDiff-diff*2))
        vel = [vel[0]*closestObj.bounciness, vel[1]*closestObj.bounciness]
        diff2Point = (closestP[0]-cPoint[0], closestP[1]-cPoint[1])
        odiff = (pos[0]-cPoint[0], pos[1]-cPoint[1])
        # HACK
        smallness = rotateBy0([0, AVERYSMALLNUMBER], phi-180-diff*2)
        newp1, newp2 = (oldLine.p1[0]+odiff[0], oldLine.p1[1]+odiff[1]), (oldLine.p2[0]+odiff[0], oldLine.p2[1]+odiff[1])
        o = self.handleCollisionsPos(
            Line((oldLine.p1[0]+diff2Point[0]+smallness[0], oldLine.p1[1]+diff2Point[1]+smallness[1]), 
                 (oldLine.p2[0]+diff2Point[0]+smallness[0], oldLine.p2[1]+diff2Point[1]+smallness[1])), 
            Line(newp1, newp2), objs, vel, False, precision, verbose)
        out, outvel = o[0], o[1]
        if replaceSelf:
            self.p1, self.p2 = out.p1, out.p2
        if verbose:
            return out, outvel, [collTyp, True]
        return out, outvel

    def handleCollisionsVel(self, 
                              vel: pointLike, 
                              objs: Union[Shapes, Iterable[Shape]], 
                              replaceSelf: bool = True, 
                              precision: Number = BASEPRECISION, 
                              verbose: bool = False
                             ) -> tuple['Line', pointLike, verboseOutput]:
        """
        Handles movement of this line via velocity and it bouncing off of other objects.

        Args:
            vel (pointLike): The velocity of this line.
            objs (Shapes / Iterable[Shape]): The objects to bounce off of.
            replaceSelf (bool, optional): Whether to move this Line to the new position after bouncing or not. Defaults to True.
            precision (Number, optional): The decimal places to round to to check (for things like corner checking). Defaults to 5.
            verbose (bool, optional): Whether to give verbose output or not. Defaults to False.

        Returns:
            tuple[Line, pointLike, veboseOutput?]: The new position and vel of this object respectively, and if verbose then the verboseOutput.
        
        VerboseOutput:
            CollisionType (list[int, ...] / None): The type of collision that occured for each sub-collision (if it ever collided, that is)
            DidReflect (bool): Whether the line reflected off of something
        """
        o = self.handleCollisionsPos(self, Line((self.p1[0]+vel[0], self.p1[1]+vel[1]), (self.p2[0]+vel[0], self.p2[1]+vel[1])), objs, vel, False, precision, verbose)
        out, outvel = o[0], o[1]
        if replaceSelf:
            self.p1, self.p2 = out.p1, out.p2
        if verbose:
            return out, outvel, o[2]
        return out, outvel
    
    def copy(self) -> 'Line':
        """
        Make a copy of the Line with the same values!
        """
        return Line(self.p1, self.p2, self.bounciness)
    
    def __getitem__(self, item: int) -> pointLike:
        if item == 0:
            return self.p1
        elif item == 1:
            return self.p2
        else:
            raise IndexError(
                'List index out of range! Must be 0-1, found: '+str(item)
            )
    
    def __setitem__(self, item: int, new: pointLike) -> None:
        if item == 0:
            self.p1 = new
        elif item == 1:
            self.p2 = new
        else:
            raise IndexError(
                'List index out of range! Must be 0-1, found: '+str(item)
            )
    
    def __iter__(self):
        return iter((self.p1, self.p2))
    
    def __str__(self):
        return f'<Line from {self.p1} to {self.p2}>'

class Circle(Shape):
    """A perfect circle. Defined as an x and y centre coordinate of the circle and a radius.
    Please be mindful when checking for this class as it is technically a closed shape, but if you try to run \
    `.toLines()` or `.toPoints()` it will return an empty list; so please check for it *before* closed shapes."""
    GROUPS = {ShpGroups.CLOSED, ShpGroups.NOTSTRAIGHT}
    TYPE = ShpTyps.Circle
    def __init__(self, x: Number, y: Number, r: Number, bounciness: float = BASEBOUNCINESS):
        """
        Args:
            x (Number): The x ordinate of the centre of this circle.
            y (Number): The y ordinate of the centre of this circle.
            r (Number): The radius of the circle
            bounciness (float, optional): How bouncy this object is. 1 = rebounds perfectly, <1 = eventually will stop, >1 = will bounce more each time. Defaults to 0.7.
        """
        super().__init__(bounciness)
        self.x, self.y, self.r = x, y, r
    
    @property
    def d(self):
        """The diameter of the circle."""
        return self.r*2

    @d.setter
    def d(self, value):
        self.r = value/2
    
    def rect(self) -> Iterable[Number]:
        """
        Returns the rectangle bounding box surrounding this circle.

        Returns:
            Iterable[Number]: (min x, min y, max x, max y)
        """
        return self.x - self.r, self.y - self.r, self.x + self.r, self.y + self.r
    
    def area(self) -> Number:
        """
        Gets the area of the circle.

        Returns:
            Number: The area of the circle.
        """
        return math.pi * self.r**2
    
    def _contains(self, othershape: Shape) -> bool:
        if checkShpType(othershape, ShpTyps.Point):
            return (self.x - othershape.x)**2 + (self.y - othershape.y)**2 < self.r**2
        if checkShpType(othershape, ShpTyps.Line):
            return self._contains(Point(*othershape.p1)) and self._contains(Point(*othershape.p2))
        if checkShpType(othershape, ShpTyps.Circle):
            return (self.x - othershape.x)**2 + (self.y - othershape.y)**2 < max(self.r-othershape.r, 0)**2
        if checkShpType(othershape, ShpTyps.Arc):
            ps = othershape.toPoints()
            return self._contains(ps[0]) and self._contains(ps[1])
        if checkShpType(othershape, ShpGroups.CLOSED):
            return all(self._contains(Point(*p)) for p in othershape.toPoints())
    
    def _collides(self, othershape: Shape) -> bool:
        if checkShpType(othershape, ShpTyps.Point):
            return (self.x - othershape.x)**2 + (self.y - othershape.y)**2 <= self.r**2
        if checkShpType(othershape, ShpTyps.Line):
            if not self.check_rects(othershape):
                return False
            # Calculate the distance from point to the line segment
            line_mag = (othershape.p2[0] - othershape.p1[0]) ** 2 + (othershape.p2[1] - othershape.p1[1]) ** 2
            if line_mag == 0:
                return (self.x - othershape.p1[0]) ** 2 + (self.y - othershape.p1[1]) ** 2 <= self.r ** 2
            
            u = ((self.x - othershape.p1[0]) * (othershape.p2[0] - othershape.p1[0]) + (self.y - othershape.p1[1]) * (othershape.p2[1] - othershape.p1[1])) / line_mag
            u = max(min(u, 1), 0)
            ix = othershape.p1[0] + u * (othershape.p2[0] - othershape.p1[0])
            iy = othershape.p1[1] + u * (othershape.p2[1] - othershape.p1[1])
            return (self.x - ix) ** 2 + (self.y - iy) ** 2 <= self.r ** 2
        if checkShpType(othershape, ShpTyps.Circle):
            return (self.x - othershape.x)**2 + (self.y - othershape.y)**2 < (self.r + othershape.r)**2
        return othershape._collides(self)
    
    def _where(self, othershape: Shape) -> Iterable[pointLike]:
        if checkShpType(othershape, ShpTyps.Point):
            return [[othershape.x, othershape.y]] if ((self.x - othershape.x)**2 + (self.y - othershape.y)**2 == self.r**2) else []
        if checkShpType(othershape, ShpTyps.Line):
            if not self.check_rects(othershape):
                return []
            def sign(x):
                return -1 if x < 0 else 1
            x1 = othershape.p1[0] - self.x
            y1 = othershape.p1[1] - self.y
            x2 = othershape.p2[0] - self.x
            y2 = othershape.p2[1] - self.y
            dx = x2 - x1
            dy = y2 - y1
            dr = math.sqrt(dx*dx + dy*dy)
            if dr == 0:
                return self.whereCollides(Point(*othershape.p1))
            D = x1 * y2 - x2 * y1
            discriminant = self.r*self.r*dr*dr - D*D
            if discriminant < 0:
                return []
            if discriminant == 0:
                xa = (D * dy ) /  (dr * dr)
                ya = (-D * dx ) /  (dr * dr)
                ta = (xa-x1)*dx/dr + (ya-y1)*dy/dr
                return [(xa + self.x, ya + self.y)] if 0 < ta < dr else []

            discRoot = math.sqrt(discriminant)
            
            xa = (D * dy + sign(dy) * dx * discRoot) / (dr * dr)
            ya = (-D * dx + abs(dy) * discRoot) / (dr * dr)
            ta = (xa-x1)*dx/dr + (ya-y1)*dy/dr
            xpt = [(xa + self.x, ya + self.y)] if 0 < ta < dr else []
            
            xb = (D * dy - sign(dy) * dx * discRoot) / (dr * dr) 
            yb = (-D * dx - abs(dy) * discRoot) / (dr * dr)
            tb = (xb-x1)*dx/dr + (yb-y1)*dy/dr
            xpt += [(xb + self.x, yb + self.y)] if 0 < tb < dr else []
            return xpt
        if checkShpType(othershape, ShpTyps.Circle):
            if not self.check_rects(othershape):
                return []
            # circle 1: (x0, y0), radius r0
            # circle 2: (x1, y1), radius r1

            d=math.hypot(othershape.x-self.x, othershape.y-self.y)
            
            # non intersecting
            if d > self.r + othershape.r :
                return []
            # One circle within other
            if d < abs(self.r-othershape.r):
                return []
            # coincident circles
            if d == 0 and self.r == othershape.r:
                return []
            else:
                r2 = self.r**2
                a=(r2-othershape.r**2+d**2)/(2*d)
                h=math.sqrt(r2-a**2)
                x2=self.x+a*(othershape.x-self.x)/d   
                y2=self.y+a*(othershape.y-self.y)/d   
                x3=x2+h*(othershape.y-self.y)/d     
                y3=y2-h*(othershape.x-self.x)/d 

                x4=x2-h*(othershape.y-self.y)/d
                y4=y2+h*(othershape.x-self.x)/d
                
                return [[x3, y3], [x4, y4]]
        return othershape._where(self)
    
    def closestPointTo(self, othershape: Shape, returnAll: bool = False) -> Union[pointLike,Iterable[pointLike]]:
        """
        Find the closest point ON this object TO another object.

        Args:
            othershape (Shape): The other object to find the closest point to
            returnAll (bool, optional): Whether to return all the possible points in order of closeness or not. Defaults to False.

        Returns:
            pointLike / Iterable[pointLike]: The closest point(s, depending on returnAll) ON this object TO the othershape
        """
        if checkShpType(othershape, ShpTyps.Point):
            x, y = othershape.x - self.x, othershape.y - self.y
            #if abs(x)**2 + abs(y)**2 < self.r**2:
            #    return othershape
            phi = (math.degrees(math.atan2(y, x)) - 90) % 360
            angle = math.radians(phi)
            
            qx = self.x - math.sin(angle) * self.r
            qy = self.y + math.cos(angle) * self.r
            if returnAll:
                return [[qx, qy]]
            return qx, qy
        elif checkShpType(othershape, ShpTyps.Line):
            if self._collides(othershape):
                wheres = self._where(othershape)
                if wheres != []:
                    if returnAll:
                        return wheres
                    return wheres[0]
                sort = sorted([othershape.p1, othershape.p2], 
                              key=lambda p: abs(self.r**2-((self.x-p[0])**2+(self.y-p[1])**2)))
                if returnAll:
                    return sort
                return sort[0]
            return self.closestPointTo(Point(*othershape.closestPointTo(Point(self.x, self.y))), returnAll)
        elif checkShpType(othershape, ShpTyps.Circle):
            return self.closestPointTo(Point(othershape.x, othershape.y), returnAll)
        elif checkShpType(othershape, ShpTyps.Arc):
            return self.closestPointTo(Point(*othershape.closestPointTo(self)), returnAll)
        else:
            ps = []
            for ln in othershape.toLines():
                ps.append(ln.closestPointTo(self))
            ps.sort(key=lambda x: (x[0]-self.x)**2+(x[1]-self.y)**2)
            if returnAll:
                return [self.closestPointTo(Point(*p)) for p in ps]
            return self.closestPointTo(Point(*ps[0]))
    
    def handleCollisionsPos(self, 
                            oldCir: 'Circle', 
                            newCir: 'Circle', 
                            objs: Union[Shapes, Iterable[Shape]], 
                            vel: pointLike = [0,0], 
                            maxTries: int = 50,
                            replaceSelf: bool = True, 
                            precision: Number = BASEPRECISION, 
                            verbose: bool = False
                           ) -> tuple[pointLike, pointLike, verboseOutput]:
        """
        Handles movement of this Circle and it bouncing off of other objects.
        It is recommended you use `.handleCollisionsVel` instead of this, as it handles velocity instead of raw movement and is easier to use.

        But if you are to use this, remember to still provide the vel param. It will sometimes provide weird results if you don't.
        It could even just be the difference in positions, it just needs to be something realistic.

        Args:
            oldCir (Circle): The old position of this object.
            newCir (Circle): The new position of this object.
            objs (Shapes / Iterable[Shape]): The objects this will bounce off.
            vel (pointLike, optional): The velocity that this object is going. Defaults to [0, 0]
            maxTries (int, optional): The maximum amount of tries it will do to get the circle to stop colliding when it hits something. Defaults to 50.
            replaceSelf (bool, optional): Whether to replace self.x and self.y with the new position of the object after bouncing or not. Defaults to True.
            precision (Number, optional): The decimal places to round to to check (for things like corner checking). Defaults to 5.
            verbose (bool, optional): Whether to give verbose output or not. Defaults to False.

        Returns:
            tuple[pointLike, pointLike, veboseOutput?]: The new position and vel of this object respectively, and if verbose then the verboseOutput.
        
        VerboseOutput:
            DidReflect (bool): Whether the line reflected off of something
        """
        velphi = math.atan2(vel[1], vel[0])
        quart = math.pi/2
        mvement = Shapes(oldCir, Polygon(
            (oldCir.x + oldCir.r * math.cos(velphi-quart), oldCir.y + oldCir.r * math.sin(velphi-quart)),
            (oldCir.x + oldCir.r * math.cos(velphi+quart), oldCir.y + oldCir.r * math.sin(velphi+quart)),
            (newCir.x + newCir.r * math.cos(velphi-quart), newCir.y + newCir.r * math.sin(velphi-quart)),
            (newCir.x + newCir.r * math.cos(velphi+quart), newCir.y + newCir.r * math.sin(velphi+quart)),
        ), newCir)
        # Don't let you move when you're in a wall
        if oldCir.collides(objs):
            if verbose:
                return oldCir, [0, 0], [True]
            return oldCir, [0, 0]
        
        if not mvement.collides(objs):
            if verbose:
                return newCir, vel, [False]
            return newCir, vel
        points = []
        nshps = Shapes()
        for o in objs:
            if mvement.isContaining(o):
                cs = o.toPoints()
            else:
                cs = o.whereCollides(mvement)
            if cs != []:
                nshps.add_shape(o)
                cs.extend([i for j in [mvement[0], mvement[2]] for i in o.closestPointTo(j, True) if Point(*i).collides(mvement)])
                points.extend(list(zip(cs, [o for _ in range(len(cs))])))
        points.sort(key=lambda x: abs(x[0][0]-oldCir[0])**2+abs(x[0][1]-oldCir[1])**2)
        closestP = points[0][0]
        closestObj = nshps
        def calculate(point):
            cpoMvemnt = Line((oldCir.x + oldCir.r * math.cos(velphi-math.pi), oldCir.y + oldCir.r * math.sin(velphi-math.pi)),
                            (newCir.x + newCir.r * math.cos(velphi), newCir.y + newCir.r * math.sin(velphi))
                            ).closestPointTo(Point(*point))
            dist_to = math.hypot(oldCir[0]-cpoMvemnt[0], oldCir[1]-cpoMvemnt[1]) - (
                math.sqrt(
                    newCir.r**2 - \
                    math.hypot(cpoMvemnt[0]-point[0], cpoMvemnt[1]-point[1])**2
                )
            )
            dist_left = (math.hypot(oldCir[0]-newCir[0], oldCir[1]-newCir[1])-dist_to)*closestObj.bounciness
            ThisClosestP = (oldCir.x + dist_to * math.cos(velphi), oldCir.y + dist_to * math.sin(velphi))
            return ThisClosestP, dist_left
        ThisClosestP, dist_left = calculate(closestP)
        tries = 0
        while tries < maxTries:
            closestP = closestObj.closestPointTo(Point(ThisClosestP[0], ThisClosestP[1]))
            ps = Circle(ThisClosestP[0], ThisClosestP[1], newCir.r).whereCollides(closestObj)
            if len(ps) < 2:
                break
            xs, ys = zip(*ps)
            diff = math.hypot(max(xs)-min(xs),(max(ys)-min(ys))**2)
            if diff < AVERYSMALLNUMBER/2: # It needs to be able to get back out
                break
            tries += 1
            ThisClosestP, dist_left = calculate(closestP)
        if dist_left <= 0:
            if verbose:
                return oldCir, [0, 0], [True]
            return oldCir, [0, 0]
        normal = math.degrees(direction(ThisClosestP, closestP))-90
        phi = math.degrees(velphi)+90
        diff = (phi-normal) % 360
        if diff > 180:
            diff = diff - 360
        pos = rotate(ThisClosestP, [ThisClosestP[0], ThisClosestP[1]+dist_left], normal-diff)
        vel = rotateBy0(vel, 180-diff*2)
        vel = [vel[0]*closestObj.bounciness, vel[1]*closestObj.bounciness]
        # HACK
        angle = direction((0, 0), vel)-quart
        qx = -math.sin(angle) * AVERYSMALLNUMBER
        qy =  math.cos(angle) * AVERYSMALLNUMBER
        smallness = (qx, qy)
        midCir = Circle(ThisClosestP[0]+smallness[0], ThisClosestP[1]+smallness[1], newCir.r)
        if midCir.collides(objs):
            # TODO: Find out why I need this and fix *that*
            if verbose:
                return oldCir, [0, 0], [True]
            return oldCir, [0, 0]
        out, outvel = self.handleCollisionsPos(midCir, Circle(*pos, oldCir.r), objs, vel, maxTries, False, precision)
        if replaceSelf:
            self.x, self.y = out[0], out[1]
        if verbose:
            return out, outvel, [True]
        return out, outvel

    def handleCollisionsVel(self, 
                            vel: pointLike, 
                            objs: Union[Shapes,Iterable[Shape]], 
                            replaceSelf: bool = True, 
                            maxTries: int = 50,
                            precision: Number = BASEPRECISION, 
                            verbose: bool = False
                           ) -> tuple['Circle', pointLike, verboseOutput]:
        """
        Handles movement of this Circle via velocity and it bouncing off of other objects.

        Args:
            vel (pointLike): The velocity of this Circle
            objs (Shapes / Iterable[Shape]): The objects to bounce off of
            replaceSelf (bool, optional): Whether or not to replace self.x and self.y with the new position. Defaults to True.
            maxTries (int, optional): The maximum amount of tries it will do to get the circle to stop colliding when it hits something. Defaults to 50.
            precision (Number, optional): The decimal places to round to to check (for things like corner checking). Defaults to 5.
            verbose (bool, optional): Whether to give verbose output or not. Defaults to False.

        Returns:
            tuple[Circle, pointLike, veboseOutput?]: The new Circle object and vel of this object respectively, and if verbose then the verboseOutput.
        
        VerboseOutput:
            DidReflect (bool): Whether the line reflected off of something
        """
        o = self.handleCollisionsPos(self, Circle(self.x+vel[0], self.y+vel[1], self.r), objs, vel, maxTries, False, precision, verbose)
        if replaceSelf:
            self.x, self.y = o[0][0], o[0][1]
        if verbose:
            return o[0], o[1], o[2]
        return o[0], o[1]
    
    def isCorner(self, point: pointLike, precision: Number = BASEPRECISION) -> bool:
        """
        Finds whether a point is on a corner of this shape. But because circles don't have any corners, this will return False.

        Args:
            point (pointLike): The point to find if it's a corner
            precision (Number, optional): The decimal places to round to to check. Defaults to 5.

        Returns:
            bool: Whether the point is on a corner of this shape
        """
        return False

    def tangent(self, point: pointLike, vel: pointLike) -> Number:
        """
        Finds the tangent on this surface to a point with a given velocity.

        Args:
            point (pointLike): The point to find the tangent of this surface from.
            vel (pointLike): Which direction the point is moving.

        Returns:
            Number: The tangent of the circle at the point. You can -90 to get the normal.
        """
        if self.x == point[0]:
            return 90
        return math.degrees(math.atan((point[1]-self.y)/(point[0]-self.x))) + (0 if self.x>point[0] else 180)

    def copy(self) -> 'Circle':
        """
        Make a replica of this object with the same object.
        """
        return Circle(self.x, self.y, self.r, self.bounciness)
    
    def __getitem__(self, item: int) -> Number:
        if item == 0:
            return self.x
        elif item == 1:
            return self.y
        elif item == 2:
            return self.r
        else:
            raise IndexError(
                'List index out of range! Must be 0-2, found: '+str(item)
            )
    
    def __setitem__(self, item: int, new: Number) -> None:
        if item == 0:
            self.x = new
        elif item == 1:
            self.y = new
        elif item == 2:
            self.r = new
        else:
            raise IndexError(
                'List index out of range! Must be 0-2, found: '+str(item)
            )
    
    def __iter__(self):
        return iter((self.x, self.y, self.r))

    def __str__(self):
        return f'<Circle @ ({self.x}, {self.y}) with radius {self.r}>'

class Arc(Circle):
    """A section of a circle's circumfrance. This is in the 'lines' group because it can be used as the outer edge of another shape.
    This is defined as an x, y and radius just like a circle, but also with a start and end angle which is used to define the portion of the circle to take.

    FIXME: Arc to arc get closest point when both end points are close to the middle of the other arc, kinda like a chain but only one half.
    
    **ANGLES ARE MEASURED IN DEGREES.**"""
    GROUPS = {ShpGroups.LINES, ShpGroups.NOTSTRAIGHT}
    TYPE = ShpTyps.Arc
    def __init__(self, 
                 x: Number, 
                 y: Number, 
                 rad: Number, 
                 startAngle: Number, 
                 endAngle: Number, 
                 precision: Number = BASEPRECISION,
                 bounciness: float = BASEBOUNCINESS
                ):
        """
        Args:
            x (Number): The x position of this arc's centre.
            y (Number): The y position of this arc's centre.
            rad (Number): The radius of the circle.
            startAngle (Number): The starting angle to take the portion of the circumfrance of. Wraps around.
            endAngle (Number): The ending angle to take the portion of the circumfrance of. Wraps around.
            precision (Number, optional): The decimal places to round to to check. Defaults to 5. \
                This is needed as almost everything requires a very precise exact check to succeed and sometimes decimal errors occur and you get \
                an equation like `10000.000000000002 == 10000.0` which is False. This is to prevent that.
            bounciness (float, optional): How bouncy this object is. 1 = rebounds perfectly, <1 = eventually will stop, >1 = will bounce more each time. Defaults to 0.7.
        """
        self.x, self.y, self.r = x, y, rad
        self.startAng, self.endAng = startAngle, endAngle
        self.precision = precision
        self.bounciness = bounciness
    
    def area(self) -> Number:
        """
        Gets the area of the shape; the length of the arc.

        Returns:
            Number: The length of the arc.
        """
        if self.endAng < self.startAng:
            diff = 360 - self.startAng + self.endAng
        else:
            diff = self.endAng - self.startAng
        return (diff/360) * 2*math.pi * self.r
    
    def _collides(self, othershape: Shape) -> bool:
        if checkShpType(othershape, ShpTyps.Point):
            if round((self.x - othershape.x)**2 + (self.y - othershape.y)**2, self.precision) != round(self.r**2, self.precision):
                return False
            angle = math.degrees(math.atan2(othershape.y - self.y, othershape.x - self.x))
            return self.angleInRange(angle)
        if checkShpType(othershape, ShpTyps.Line, ShpTyps.Circle):
            if checkShpType(othershape, ShpTyps.Circle):
                if any(othershape._collides(Point(*i)) for i in self.endPoints()):
                    return True
            intersections = Circle(self.x, self.y, self.r).whereCollides(othershape)
            for pt in intersections:
                if self._collides(Point(*pt)):
                    return True
            return False
        if checkShpType(othershape, ShpTyps.Arc):
            intersections = Circle(self.x, self.y, self.r).whereCollides(othershape)
            for pt in intersections:
                p = Point(*pt)
                if self._collides(p) and othershape._collides(p):
                    return True
            return False
        return othershape._collides(self)

    def flip(self):
        """
        Flips the portion taken to make the arc; so an arc covering 90 degrees of the circle will now cover 270, and vice versa.
        """
        self.startAng, self.endAng = self.endAng, self.startAng

    def _contains(self, othershape: Shape) -> bool:
        return False
    
    def _where(self, othershape: Shape) -> Iterable[pointLike]:
        if checkShpType(othershape, ShpTyps.Point):
            if self._collides(othershape):
                return [(othershape.x, othershape.y)]
            return []
        if checkShpType(othershape, ShpTyps.Line, ShpTyps.Circle):
            intersections = Circle(self.x, self.y, self.r).whereCollides(othershape)
            return [pt for pt in intersections if self._collides(Point(*pt))]
        if checkShpType(othershape, ShpTyps.Arc):
            intersections = Circle(self.x, self.y, self.r).whereCollides(othershape)
            return [pt for pt in intersections if self._collides(Point(*pt)) and othershape._collides(Point(*pt))]
        return othershape._where(self)
    
    def closestPointTo(self, othershape: Shape, returnAll: bool = False) -> pointLike|Iterable[pointLike]:
        """
        Finds the closest point ON THIS OBJECT **TO** the other object

        Args:
            othershape (Shape): The other shape to find the closest point to
            returnAll (bool, optional): Whether to return *all* the potential closest points sorted in order of closeness or just **the** closest. Defaults to False (only the closest).

        Returns:
            pointLike|Iterable[pointLike]: The closest point(s) on this object to the other object. Whether this is an iterable or not depends on the `returnAll` parameter.
        """
        if checkShpType(othershape, ShpTyps.Point):
            x, y = othershape.x - self.x, othershape.y - self.y
            #if abs(x)**2 + abs(y)**2 < self.r**2:
            #    return othershape
            phi = self.constrainAng(math.degrees(math.atan2(y, x)))
            
            angle = math.radians(phi-90)
            
            qx = self.x - math.sin(angle) * self.r
            qy = self.y + math.cos(angle) * self.r
            if returnAll:
                return [[qx, qy]]
            return qx, qy
        elif checkShpType(othershape, ShpTyps.Line):
            cirO = Circle(self.x, self.y, self.r)
            if cirO.collides(othershape):
                def checkP(p, this):
                    if not this:
                        p = self.closestPointTo(Point(*p))
                    op = othershape.closestPointTo(Point(*p))
                    return (p, (op[0]-p[0])**2+(op[1]-p[1])**2)
                alls = [
                    checkP(i, True) for i in self.endPoints()
                ] + [
                    checkP(i, False) for i in othershape.toPoints()
                ] + [
                    checkP(i, False) for i in cirO.whereCollides(othershape)
                ]
                alls.sort(key=lambda i: i[1])
                if returnAll:
                    return [i[0] for i in alls]
                return alls[0][0]
            return self.closestPointTo(Point(*cirO.closestPointTo(othershape)), returnAll)
        elif checkShpType(othershape, ShpTyps.Circle):
            return self.closestPointTo(Point(othershape.x, othershape.y), returnAll)
        elif checkShpType(othershape, ShpTyps.Arc):
            wheres = self.whereCollides(othershape)
            if wheres != []:
                if returnAll:
                    return wheres
                return wheres[0]
            x, y = self.x - othershape.x, self.y - othershape.y
            phi = (math.degrees(math.atan2(y, x)))
            if Circle(self.x, self.y, self.r).collides(othershape):
                phi -= 180
            angle = math.radians(othershape.constrainAng(phi%360)-90)
            
            qx = othershape.x - math.sin(angle) * othershape.r
            qy = othershape.y + math.cos(angle) * othershape.r
            
            x, y = qx - self.x, qy - self.y
            phi = (math.degrees(math.atan2(y, x))) % 360
            angle = math.radians(self.constrainAng(phi)-90)
            
            qx = self.x - math.sin(angle) * self.r
            qy = self.y + math.cos(angle) * self.r
            if returnAll:
                return [[qx, qy]]
            return qx, qy
        else:
            closests = []
            for ln in othershape.toLines():
                cp = self.closestPointTo(ln)
                ocp = othershape.closestPointTo(Point(*cp))
                d = (cp[0]-ocp[0])**2+(cp[1]-ocp[1])**2
                closests.append((cp, d))
            closests.sort(key=lambda x: x[1])
            if returnAll:
                return [i[0] for i in closests]
            return closests[0][0]
    
    def constrainAng(self, phi: Number) -> Number:
        self.startAng, self.endAng = self.startAng % 360, self.endAng % 360
        phi = phi % 360
        def angular_distance(a, b):
            return min(abs(a - b), 360 - abs(a - b))
        if self.endAng < self.startAng:
            if phi < self.startAng and phi > self.endAng:
                dist_to_start = angular_distance(phi, self.startAng)
                dist_to_end = angular_distance(phi, self.endAng)
                return self.startAng if dist_to_start < dist_to_end else self.endAng
        else:
            if phi > self.endAng or phi < self.startAng:
                dist_to_start = angular_distance(phi, self.startAng)
                dist_to_end = angular_distance(phi, self.endAng)
                if dist_to_start < dist_to_end:
                    return self.startAng
                else:
                    return self.endAng
        return phi

    def angleInRange(self, angle: Number) -> bool:
        """
        Check to see if an angle is in the range of this arc.

        Args:
            angle (Number): The angle to check if it is in range of this arc or not.

        Returns:
            bool: Whether or not the angle is in the range of this arc.
        """
        self.startAng, self.endAng = self.startAng % 360, self.endAng % 360
        if self.startAng > self.endAng:
            return angle%360 >= self.startAng or angle%360 <= self.endAng
        else:
            return self.startAng <= angle%360 <= self.endAng
    
    def endPoints(self) -> Iterable[pointLike]:
        """
        Gets the end points of the arc

        Returns:
            Iterable[pointLike]: The endpoints of the arc
        """
        startAng = math.radians(self.startAng)
        endAng = math.radians(self.endAng)
        return (self.x + self.r * math.cos(startAng), self.y + self.r * math.sin(startAng)), \
               (self.x + self.r * math.cos(endAng), self.y + self.r * math.sin(endAng))

    def rect(self) -> Iterable[Number]:
        """
        Returns the rectangle bounding box surrounding this object.

        Returns:
            Iterable[Number]: (min x, min y, max x, max y)
        """
        eps = self.endPoints()
        
        if self.angleInRange(270):
            N = self.y-self.r
        else:
            N = min(eps[0][1], eps[1][1])
        if self.angleInRange(180):
            E = self.x-self.r
        else:
            E = min(eps[0][0], eps[1][0])
        if self.angleInRange(90):
            S = self.y+self.r
        else:
            S = max(eps[0][1], eps[1][1])
        if self.angleInRange(0):
            W = self.x+self.r
        else:
            W = max(eps[0][0], eps[1][0])
        return E, N, W, S
    
    def isCorner(self, point: pointLike, precision: Number = BASEPRECISION) -> bool:
        """
        Finds whether a point is on a corner of this shape.

        Args:
            point (pointLike): The point to find if it's a corner
            precision (Number, optional): The decimal places to round to to check. Defaults to 5.

        Returns:
            bool: Whether the point is on a corner of this shape
        """
        for p in self.toPoints():
            if round(p[0], precision) == round(point[0], precision) and \
               round(p[1], precision) == round(point[1], precision):
                return True
        return False

    def toPoints(self):
        """
        Returns:
            Iterable[pointLike]: Get a list of all the Points that make up this object.
        """
        return [
            Point(*rotate((self.x, self.y), (self.x, self.y+self.r), self.startAng-90)),
            Point(*rotate((self.x, self.y), (self.x, self.y+self.r), self.endAng-90)),
        ]
    
    def copy(self) -> 'Arc':
        """
        Because Noah's first arc broke, now you need another one.
        """
        return Arc(self.x, self.y, self.r, self.startAng, self.endAng, self.precision, self.bounciness)
    
    def __getitem__(self, item: int) -> Union[Number, pointLike]:
        if item == 0:
            return self.x
        elif item == 1:
            return self.y
        elif item == 2:
            return self.r
        elif item == 3:
            return self.startAng
        elif item == 4:
            return self.endAng
        else:
            raise IndexError(
                'List index out of range! Must be 0-4, found: '+str(item)
            )
    
    def __setitem__(self, item: int, new: Union[Number, pointLike]) -> None:
        if item == 0:
            self.x = new
        elif item == 1:
            self.y = new
        elif item == 2:
            self.r = new
        elif item == 3:
            self.startAng = new
        elif item == 4:
            self.endAng = new
        else:
            raise IndexError(
                'List index out of range! Must be 0-4, found: '+str(item)
            )
    
    def __iter__(self):
        return iter((self.x, self.y, self.r, self.startAng, self.endAng))
    
    def __str__(self):
        return f'<Arc @ ({self.x}, {self.y}) with radius {self.r} and angles between {self.startAng}°-{self.endAng}°>'

class ClosedShape(Shape):
    """These are shapes like rects and polygons; if you split them into a list of lines all the lines join with one another.
    Please do not use this class as it is just a building block for subclasses and to provide them with some basic methods."""
    GROUPS = {ShpGroups.CLOSED, ShpGroups.SPLITTABLE}
    def _where(self, othershape: Shape) -> Iterable[pointLike]:
        if not self.check_rects(othershape):
            return []
        if checkShpType(othershape, ShpTyps.Point):
            for i in self.toLines():
                if i.collides(othershape):
                    return [[othershape.x, othershape.y]]
            return []
        else:
            points = []
            for i in self.toLines():
                points.extend(i._where(othershape))
            return points
    
    def tangent(self, point: pointLike, vel: pointLike) -> Number:
        """
        Finds the tangent on this surface to a point with a given velocity.

        Args:
            point (pointLike): The point to find the tangent of this surface from.
            vel (pointLike): Which direction the point is moving. In this case (for closed shapes, which are made of lines) it is actually very important, so please don't forget it.

        Returns:
            Number: The tangent of the line at the point. You can -90 to get the normal.
        """
        # TODO: Make it so the line normals go in the direction facing away from the centre instead of away from the velocity vector 
        p = Point(*point)
        ps = [[i.closestPointTo(p), i] for i in self.toLines()]
        origps = [[pt[1].tangent(pt[0], vel), pt[0]] for pt in ps]
        ps = origps.copy()
        ps.sort(key=lambda x: abs(x[1][0]-point[0])**2+abs(x[1][1]-point[1])**2)
        if ps[0][1] == ps[1][1]:
            def degrees_to_vector(angle):
                # Convert an angle to a unit vector
                radians = math.radians(angle)
                return math.cos(radians), math.sin(radians)

            # Convert both angles to vectors
            x1, y1 = degrees_to_vector(ps[0][0])
            x2, y2 = degrees_to_vector(ps[1][0])
            
            # Average the x and y components
            avg_x = (x1 + x2) / 2
            avg_y = (y1 + y2) / 2
            return math.degrees(math.atan2(avg_y, avg_x)) % 360
        
        return ps[0][0]
    
    def closestPointTo(self, othershape: Shape, returnAll: bool = False) -> Union[pointLike, Iterable[pointLike]]:
        """
        Find the closest point ON this object TO another object.

        Args:
            othershape (Shape): The other object to find the closest point to
            returnAll (bool, optional): Whether to return all the possible points in order of closeness or not. Defaults to False.

        Returns:
            pointLike / Iterable[pointLike]: The closest point(s, depending on returnAll) ON this object TO the othershape
        """
        if checkShpType(othershape, ShpTyps.Point):
            ps = [i.closestPointTo(othershape) for i in self.toLines()]
            ps.sort(key=lambda x: abs(x[0]-othershape[0])**2+abs(x[1]-othershape[1])**2)
            if returnAll:
                return ps
            return ps[0]
        elif checkShpType(othershape, ShpTyps.Line):
            colls = self.whereCollides(othershape)
            if colls != []:
                if returnAll:
                    return colls
                return colls[0]
            def calculate(ln, oln, recalculate):
                p2 = oln.closestPointTo(ln)
                p = ln.closestPointTo(Point(*p2))
                if recalculate:
                    p3 = oln.closestPointTo(Point(*p))
                    p2 = p
                    p = p3
                return p2, abs(p[0]-p2[0])**2+abs(p[1]-p2[1])**2
            tries = [
                calculate(othershape, p, False) for p in self.toLines()
            ] + [
                calculate(ln, othershape, True) for ln in self.toLines()
            ]
            tries.sort(key=lambda x: x[1])
            if returnAll:
                return [i[0] for i in tries]
            return tries[0][0]
        elif checkShpType(othershape, ShpTyps.Circle):
            return self.closestPointTo(Point(othershape.x, othershape.y), returnAll)
        elif checkShpType(othershape, ShpTyps.Arc):
            closests = []
            for ln in self.toLines():
                cp = othershape.closestPointTo(ln)
                mycp = self.closestPointTo(Point(*cp))
                d = (cp[0]-mycp[0])**2+(cp[1]-mycp[1])**2
                closests.append((mycp, d))
            closests.sort(key=lambda x: x[1])
            if returnAll:
                return [i[0] for i in closests]
            return closests[0][0]
        else:
            colls = self.whereCollides(othershape)
            if colls != []:
                if returnAll:
                    return colls
                return colls[0]
            def calculate(ln, point, recalculate):
                p2 = ln.closestPointTo(Point(*point))
                olineP = point
                if recalculate:
                    olineP = p2
                    p2 = self.closestPointTo(Point(*p2))
                return p2, abs(p2[0]-olineP[0])**2+abs(p2[1]-olineP[1])**2
            tries = []
            olns = othershape.toLines()
            slns = self.toLines()
            for ln in slns:
                tries.extend([calculate(ln, oln.p1, False) for oln in olns])
                tries.extend([calculate(ln, oln.p2, False) for oln in olns])
            for oln in olns:
                tries.extend([calculate(oln, ln.p1, True) for ln in slns])
                tries.extend([calculate(oln, ln.p2, True) for ln in slns])
            tries.sort(key=lambda x: x[1])
            if returnAll:
                return [i[0] for i in tries]
            return tries[0][0]
    
    def handleCollisionsPos(self, 
                            oldShp: 'ClosedShape', 
                            newShp: 'ClosedShape', 
                            objs: Union[Shapes, Iterable[Shape]], 
                            vel: pointLike = [0, 0], 
                            replaceSelf: bool = True, 
                            precision: Number = BASEPRECISION, 
                            verbose: bool = False
                           ) -> tuple['ClosedShape', pointLike, verboseOutput]:
        """
        Handles movement of this closed shape and it bouncing off of other objects.
        It is recommended you use `.handleCollisionsVel` instead of this, as it handles velocity instead of raw movement and is easier to use.

        But if you are to use this, remember to still provide the vel param. It will provide VERY weird results if you don't.
        It could even just be the difference in positions, it just needs to be something realistic.

        Args:
            oldShp (ClosedShape): The old object.
            newShp (ClosedShape): The new object. Should be the exact same as the old one except with the points offset by the same amount.
            objs (Shapes / Iterable[Shape]): The objects this will bounce off.
            vel (pointLike, optional): The velocity that this object is going. Defaults to [0, 0].
            replaceSelf (bool, optional): Whether to move this object to the new position after bouncing or not. Defaults to True.
            precision (Number, optional): The decimal places to round to to check (for things like corner checking). Defaults to 5.
            verbose (bool, optional): Whether to give verbose output or not. Defaults to False.

        Returns:
            tuple[ClosedShape, pointLike, veboseOutput?]: The new object and vel respectively, and if verbose then the verboseOutput.
        
        VerboseOutput:
            CollisionType (list[int, ...] / None): The type of collision that occured for each sub-collision (if it ever collided, that is)
            DidReflect (bool): Whether the object reflected off of something
        """
        # Don't let you move when you're in a wall, but if you are leaving a wall then GET THE HELLA OUTTA THERE
        if oldShp.collides(objs):
            if newShp.collides(objs):
                if verbose:
                    return oldShp, [0, 0], [None, True]
                return oldShp, [0, 0]
            else:
                if verbose:
                    return newShp, vel, [None, False]
                return newShp, vel
        points = []
        hit = False
        for oldLine, newLine in zip(oldShp.toLines(), newShp.toLines()):
            oldLine = Line(*sorted([oldLine.p1, oldLine.p2], key=lambda x: x[0]))
            newLine = Line(*sorted([newLine.p1, newLine.p2], key=lambda x: x[0]))
            mvement = Polygon(oldLine.p1, oldLine.p2, newLine.p2, newLine.p1)
            for o in objs:
                if o.collides(mvement):
                    hit = True
                    ps = o.whereCollides(mvement) + [i for i in o.closestPointTo(oldLine, True) if mvement.collides(Point(*i))]
                    for p in ps:
                        if oldShp.collides(Point(*p)):
                            continue
                        # The rotation is making sure the line crosses the oldLine
                        cPoint = oldLine.closestPointTo(Line(p, (p[0]-vel[0],p[1]-vel[1])))
                        pdists = (oldLine.p1[0]-p[0])**2+(oldLine.p1[1]-p[1])**2 + (oldLine.p2[0]-p[0])**2+(oldLine.p2[1]-p[1])**2
                        points.append([p, o, cPoint, round((p[0]-cPoint[0])**2+(p[1]-cPoint[1])**2, precision), round(pdists, precision), oldLine, newLine])
                        #points.extend(list(zip(cs, [o for _ in range(len(cs))])))
        if not hit:
            if verbose:
                return newShp, vel, [None, False]
            return newShp, vel
        # Don't let you move when you're in a wall
        if points == []:
            if verbose:
                return oldShp, [0, 0], [None, True]
            return oldShp, [0, 0]
        
        points.sort(key=lambda x: (x[3], x[4]))
        oldLine, newLine = points[0][5], points[0][6]
        closestP = points[0][0] # Closest point on the OTHER object
        cPoint = points[0][2] # closestP projected onto the oldLine
        closestObj = points[0][1]
        newPoint = newLine.closestPointTo(Line(closestP, (closestP[0]+vel[0],closestP[1]+vel[1]))) # closestP projected onto the newLine

        thisNormal = math.degrees(math.atan2(oldLine[0][1]-oldLine[1][1], oldLine[0][0]-oldLine[1][0]))
        paralell = False
        thisIsOnP = oldLine.isCorner(cPoint, precision)
        if checkShpType(closestObj, ShpGroups.NOTSTRAIGHT):
            paralell = not thisIsOnP
        else:
            cLines = []
            if checkShpType(closestObj, ShpTyps.Line):
                cLines = [closestObj]
            elif checkShpType(closestObj, ShpGroups.CLOSED):
                cLines = [i for i in closestObj.toLines() if i.collides(Point(*closestP))]
            elif checkShpType(closestObj, ShpTyps.Circle) and (not thisIsOnP):
                paralell = True
            if cLines != []:
                for cLine in cLines:
                    sortedOtherLn = Line(*sorted([cLine.p1, cLine.p2], key=lambda x: x[0]))
                    otherLnNormal = math.degrees(math.atan2(sortedOtherLn[0][1]-sortedOtherLn[1][1], sortedOtherLn[0][0]-sortedOtherLn[1][0]))
                    paralell = abs(otherLnNormal%360 - thisNormal%360) < precision or abs((otherLnNormal-180)%360 - thisNormal%360) < precision
                    if paralell:
                        break
        velDiff = 180
        if paralell: # Line off line
            collTyp = 3
            # Reflect off the object's normal to the point (but really could be either point; the tangents *should* be the same)
            normal = thisNormal
            phi = math.degrees(math.atan2(newPoint[1] - closestP[1], newPoint[0] - closestP[0]))-90
        else:
            otherIsOnP = closestObj.isCorner(closestP, precision)
            if thisIsOnP and otherIsOnP: # Point off point collision
                collTyp = 0
                # Reflect off the same way as you came in (as if you can land an infintesimally small point on another infintesimally small point anyway)
                normal, phi = 0, 0
            elif thisIsOnP and (not otherIsOnP): # Point off line
                collTyp = 1
                # Reflect off the other object's normal to the point
                normal = closestObj.tangent(closestP, vel)-90
                phi = math.degrees(math.atan2(newPoint[1] - closestP[1], newPoint[0] - closestP[0]))-90 # The angle of incidence
            elif (not thisIsOnP) and otherIsOnP: # Line off point
                collTyp = 2
                # Reflect off this line's normal
                normal = thisNormal-90 # The normal off the line
                phi = math.degrees(math.atan2(closestP[1] - newPoint[1], closestP[0] - newPoint[0]))-90 # The angle of incidence
                velDiff = 0
            else:
                #raise TypeError(
                #    'Cannot have a line reflecting off of another line when they aren\'t paralell; something bad must have occured!'
                #)
                collTyp = None
                normal, phi = 0, 0
        
        if round(newPoint[0], precision) == round(closestP[0], precision) and round(newPoint[1], precision) == round(closestP[1], precision):
            phi = normal+180

        # the distance between the closest point on the other object and the corresponding point on the newLine
        dist_left = math.hypot(newPoint[0]-closestP[0], newPoint[1]-closestP[1]) * closestObj.bounciness
        diff = (phi-normal) % 360 # The difference between the angle of incidence and the normal
        if diff > 180: # Do we even need this?
            diff -= 360
        pos = rotate(closestP, [closestP[0], closestP[1] + dist_left], phi-180-diff*2)
        vel = list(rotateBy0(vel, velDiff-diff*2))
        vel = [vel[0]*closestObj.bounciness, vel[1]*closestObj.bounciness]
        diff2Point = (closestP[0]-cPoint[0], closestP[1]-cPoint[1])
        odiff = (pos[0]-cPoint[0], pos[1]-cPoint[1])
        smallness = rotateBy0([0, AVERYSMALLNUMBER], phi-180-diff*2) # HACK
        newobj = self.copy()
        newobj.x, newobj.y = newobj.x+odiff[0], newobj.y+odiff[1]
        intermediateObj = self.copy()
        intermediateObj.x, intermediateObj.y = oldShp.x+diff2Point[0]+smallness[0], oldShp.y+diff2Point[1]+smallness[1]
        o = self.handleCollisionsPos(intermediateObj, newobj, objs, vel, False, precision, verbose)
        out, outvel = o[0], o[1]
        if replaceSelf:
            self.x, self.y = out.x, out.y
        if verbose:
            return out, outvel, [collTyp, True]
        return out, outvel

    def handleCollisionsVel(self,
                              vel: pointLike,
                              objs: Union[Shapes, Iterable[Shape]],
                              replaceSelf: bool = True,
                              precision: Number = BASEPRECISION,
                              verbose: bool = False
                             ) -> tuple['ClosedShape', pointLike, verboseOutput]:
        """
        Handles movement of this object via velocity and it bouncing off of other objects.

        Args:
            vel (pointLike): The velocity of this object.
            objs (Shapes / Iterable[Shape]): The objects to bounce off of.
            replaceSelf (bool, optional): Whether to move this object to the new position after bouncing or not. Defaults to True.
            precision (Number, optional): The decimal places to round to to check (for things like corner checking). Defaults to 5.
            verbose (bool, optional): Whether to give verbose output or not. Defaults to False.

        Returns:
            tuple[ClosedShape, pointLike, veboseOutput?]: The new position and vel of this object respectively, and if verbose then the verboseOutput.
        
        VerboseOutput:
            CollisionType (list[int, ...] / None): The type of collision that occured for each sub-collision (if it ever collided, that is)
            DidReflect (bool): Whether the line reflected off of something
        """
        n = self.copy()
        n.x, n.y = n.x+vel[0], n.y+vel[1]
        o = self.handleCollisionsPos(self, n, objs, vel, False, precision, verbose)
        out, outvel = o[0], o[1]
        if replaceSelf:
            self.x, self.y = out.x, out.y
        if verbose:
            return out, outvel, o[2]
        return out, outvel
    
    def _containsPoint(self, point: Point) -> bool:
        return self._collides(point) and self.whereCollides(point) == []

    def _contains(self, othershape: Shape) -> bool:
        if checkShpType(othershape, ShpTyps.Point):
            return self._containsPoint(othershape)
        if checkShpType(othershape, ShpTyps.Line):
            return self._contains(Point(*othershape.p1)) and self._contains(Point(*othershape.p2))
        if checkShpType(othershape, ShpTyps.Circle) or checkShpType(othershape, ShpTyps.Arc):
            return self._collides(othershape) and self.whereCollides(othershape) == []
        if checkShpType(othershape, ShpGroups.CLOSED):
            return all(self._contains(Point(*p)) for p in othershape.toPoints())
    
    def isCorner(self, point: pointLike, precision: Number = BASEPRECISION) -> bool:
        """
        Finds whether a point is on a corner of this shape.

        Args:
            point (pointLike): The point to find if it's a corner
            precision (Number, optional): The decimal places to round to to check. Defaults to 5.

        Returns:
            bool: Whether the point is on a corner of this shape
        """
        for i in self.toPoints():
            if round(i[0], precision) == round(point[0], precision) and round(i[1], precision) == round(point[1], precision):
                return True
        return False
    
    def toLines(self) -> Iterable[Line]:
        """
        Returns:
            Iterable[Line]: Get a list of all the Lines that make up this object
        """
        return []
    
    def toPoints(self) -> Iterable[pointLike]:
        """
        Returns:
            Iterable[pointLike]: Get a list of all the Points that make up this object
        """
        return []
    
    def __getitem__(self, item: int) -> pointLike:
        return self.toPoints()[item]
    
    def __iter__(self):
        return iter(self.toPoints())

    def __str__(self):
        return '<Closed Shape>'

class Rect(ClosedShape):
    """A Rectangle. It is defined with an x, y, width and height."""
    TYPE = ShpTyps.Rect
    def __init__(self, x: Number, y: Number, w: Number, h: Number, bounciness: float = BASEBOUNCINESS):
        """
        Args:
            x (Number): The x ordinate.
            y (Number): The y ordinate.
            w (Number): The width.
            h (Number): The height.
            bounciness (float, optional): How bouncy this object is. 1 = rebounds perfectly, <1 = eventually will stop, >1 = will bounce more each time. Defaults to 0.7.
        """
        super().__init__(bounciness)
        self.x, self.y, self.w, self.h = x, y, w, h
    
    def rect(self) -> Iterable[Number]:
        """
        Returns the rectangle bounding box surrounding this rectangle, which is virtually just the rectangle itself in a different form.

        Returns:
            Iterable[Number]: (min x, min y, max x, max y)
        """
        return min(self.x, self.x + self.w), min(self.y, self.y + self.h), max(self.x, self.x + self.w), max(self.y, self.y + self.h)
    
    def area(self) -> Number:
        """
        Gets the area of the shape; width * height.

        Returns:
            Number: self.w * self.h
        """
        return self.w * self.h
    
    def _containsPoint(self, point: Point) -> bool:
        x, y, mx, my = self.rect()
        return x < point.x < mx and y < point.y and my > point.y
    
    def _collides(self, othershape: Shape) -> bool:
        x, y, mx, my = self.rect()
        if checkShpType(othershape, ShpTyps.Point):
            return x <= othershape.x <= mx and y <= othershape.y and my >= othershape.y
        if checkShpType(othershape, ShpTyps.Line):
            return self.check_rects(othershape) and (
                   (x < othershape.p1[0] and mx > othershape.p1[0] and y < othershape.p1[1] and my > othershape.p1[1]) or \
                   (x < othershape.p2[0] and mx > othershape.p2[0] and y < othershape.p2[1] and my > othershape.p2[1]) or \
                   any([i.collides(othershape) for i in self.toLines()])
            )
        if checkShpType(othershape, ShpTyps.Circle):
            return self.check_rects(othershape) and (
                   (x - othershape.r < othershape.x and mx + othershape.r > othershape.x and y < othershape.y and my > othershape.y) or \
                   (x < othershape.x and mx > othershape.x and y - othershape.r < othershape.y and my + othershape.r > othershape.y) or \
                   ((x - othershape.x)**2 + (y - othershape.y)**2 < othershape.r**2) or \
                   (((mx) - othershape.x)**2 + (y - othershape.y)**2 < othershape.r**2) or \
                   ((x - othershape.x)**2 + ((my) - othershape.y)**2 < othershape.r**2) or \
                   (((mx) - othershape.x)**2 + ((my) - othershape.y)**2 < othershape.r**2)
            )
        if checkShpType(othershape, ShpTyps.Arc):
            if any(self._collides(Point(*i)) for i in othershape.endPoints()):
                return True
            for i in self.toLines():
                if othershape.collides(i):
                    return True
            return False
        if checkShpType(othershape, ShpTyps.Rect):
            ox, oy, omx, omy = othershape.rect()
            return x <= omx and mx >= ox and y <= omy and my >= oy
        return othershape._collides(self)
    
    def toLines(self) -> Iterable[Line]:
        """
        Returns:
            Iterable[Line]: Get a list of all the Lines that make up this object
        """
        return [
            Line((self.x, self.y), (self.x + self.w, self.y)),
            Line((self.x + self.w, self.y), (self.x + self.w, self.y + self.h)),
            Line((self.x + self.w, self.y + self.h), (self.x, self.y + self.h)),
            Line((self.x, self.y + self.h), (self.x, self.y))
        ]
    
    def toPoints(self) -> Iterable[pointLike]:
        """
        Returns:
            Iterable[pointLike]: Get a list of all the Points that make up this object
        """
        return [
            [self.x, self.y],
            [self.x + self.w, self.y],
            [self.x + self.w, self.y + self.h],
            [self.x, self.y + self.h]
        ]
    
    def copy(self) -> 'Rect':
        """
        Clone this object using the latest cloning technology.
        """
        return Rect(self.x, self.y, self.w, self.h, self.bounciness)
    
    def __setitem__(self, item: int, new: pointLike) -> None:
        if item == 0:
            self.x, self.y = new[0], new[1]
        elif item == 1:
            self.x, self.y = new[0]-self.w, new[1]
        elif item == 2:
            self.x, self.y = new[0]-self.w, new[1]-self.h
        elif item == 3:
            self.x, self.y = new[0], new[1]-self.h
        else:
            raise IndexError(
                'List index out of range! Must be 0-3, found: '+str(item)
            )
    
    def __str__(self):
        return f'<Rect @ ({self.x}, {self.y}) with dimensions {self.w}x{self.h}>'

class RotatedRect(ClosedShape):
    """A rectangle...... That is rotated.
    It is rotated around it's x and y coordinates.
    Defined as an x, y, width, height and rotation."""
    TYPE = ShpTyps.RotRect
    def __init__(self, x: Number, y: Number, w: Number, h: Number, rotation: Number, bounciness: float = BASEBOUNCINESS):
        """
        Args:
            x (Number): The x ordinate. Also what it rotates around.
            y (Number): The y ordinate. Also what it rotates around.
            w (Number): The width of the object.
            h (Number): The height of the object.
            rotation (Number): The rotation of the object.
            bounciness (float, optional): How bouncy this object is. 1 = rebounds perfectly, <1 = eventually will stop, >1 = will bounce more each time. Defaults to 0.7.
        """
        super().__init__(bounciness)
        self.x, self.y, self.w, self.h, self.rot = x, y, w, h, rotation
        self.cachedPoints = []
        self.cacheRequirements = []
    
    def getCache(self) -> Iterable[pointLike]:
        """
        Specifically for the rotatedRect. This is a utility function to cache the rotated points so it doesn't have to re-rotate them every time.
        Please don't use this in your code unless you know what you're doing. Instead, use `.toPoints()` or `.toLines()`.

        Returns:
            Iterable[pointLike]: All the points that make up this rectangle, all rotated BUT NOT TRANSLATED. You must add (self.x, self.y) to each one to get the pos.
        """
        check = [self.w, self.h, self.rot]
        if check != self.cacheRequirements:
            self.cacheRequirements = check
            angle = math.radians(self.rot)
            cos = math.cos(angle)
            sin = math.sin(angle)
            def rot(x, y):
                return cos * x - sin * y, sin * x + cos * y
            self.cache = [
                (0, 0),
                rot(self.w, 0),
                rot(self.w, self.h),
                rot(0, self.h)
            ]
        return [[i[0]+self.x, i[1]+self.y] for i in self.cache]
    
    def rect(self) -> Iterable[Number]:
        """
        Returns the rectangle bounding box surrounding this rectangle.

        Returns:
            Iterable[Number]: (min x, min y, max x, max y)
        """
        ps = self.toPoints()
        return min([i[0] for i in ps]), min([i[1] for i in ps]), max([i[0] for i in ps]), max([i[1] for i in ps])
    
    def area(self) -> Number:
        """
        Gets the area of the shape; width * height.

        Returns:
            Number: self.w * self.h
        """
        return self.w * self.h
    
    def _containsPoint(self, point: Point) -> bool:
        newp = rotate((self.x, self.y), point, -self.rot)
        return self.x < newp[0] < (self.x+self.w) and self.y < newp[1] < (self.y+self.h)
    
    def _collides(self, othershape: Shape) -> bool:
        if not self.check_rects(othershape):
            return False
        if checkShpType(othershape, ShpTyps.Point):
            newp = rotate((self.x, self.y), othershape, -self.rot)
            return self.x <= newp[0] <= (self.x+self.w) and self.y <= newp[1] <= (self.y+self.h)
        if checkShpType(othershape, ShpTyps.Line):
            for li in self.toLines():
                if li.collides(othershape):
                    return True
            if self._collides(Point(*othershape.p1)) or self._collides(Point(*othershape.p2)):
                return True
            return False
        if checkShpType(othershape, ShpTyps.Circle):
            if self._collides(Point(othershape.x, othershape.y)):
                return True
            for li in self.toLines():
                if li.collides(othershape):
                    return True
            return False
        if checkShpType(othershape, ShpTyps.Arc):
            if any(self._collides(Point(*i)) for i in othershape.endPoints()):
                return True
            for i in self.toLines():
                if othershape.collides(i):
                    return True
            return False
        if checkShpType(othershape, ShpTyps.Rect, ShpTyps.RotRect):
            for li in self.toLines():
                if li.collides(othershape):
                    return True
            return othershape.collides(Point(self.x, self.y)) or self.collides(Point(othershape.x, othershape.y))
        return othershape._collides(self)
    
    def toPoints(self) -> Iterable[pointLike]:
        """
        Returns:
            Iterable[pointLike]: Get a list of all the Points that make up this object
        """
        return self.getCache()

    def toLines(self) -> Iterable[Line]:
        """
        Returns:
            Iterable[Line]: Get a list of all the Lines that make up this object
        """
        ps = self.getCache()
        return [
            Line(ps[i], ps[i+1])
            for i in range(len(ps)-1)
        ] + [Line(ps[len(ps)-1], ps[0])]
    
    def copy(self) -> 'RotatedRect':
        """
        Spawn in a duplicate object
        """
        return RotatedRect(self.x, self.y, self.w, self.h, self.rot, self.bounciness)
    
    def __setitem__(self, item: int, new: pointLike) -> None:
        def rot(x, y):
            return rotate([self.x, self.y], [x, y], self.rot)
        if item == 0:
            self.x, self.y = rot(new[0], new[1])
        elif item == 1:
            self.x, self.y = rot(new[0], new[1])
            self.x -= self.w
        elif item == 2:
            self.x, self.y = rot(new[0], new[1])
            self.x -= self.w
            self.y -= self.h
        elif item == 3:
            self.x, self.y = rot(new[0], new[1])
            self.y -= self.h
        else:
            raise IndexError(
                'List index out of range! Must be 0-3, found: '+str(item)
            )
    
    def __str__(self):
        return f'<RotatedRect @ ({self.x}, {self.y}), with dimensions {self.w}x{self.h}, rotated {self.rot}° to have points {self.toPoints()}>'

class Polygon(ClosedShape):
    """A convex or concave polygon. It is defined with a list of points."""
    TYPE = ShpTyps.Polygon
    def __init__(self, *points: pointLike, errorOnLT3: bool = True, bounciness: float = BASEBOUNCINESS):
        """
        Args:
            *points (pointLike): The points that make up the polygon.
            errorOnLT3 (bool, optional): Whether to error if the amount of points making up this polygon is less than 3. \
                If it *is* less than 3, I have no clue what will happen; it will probably get a lot of things wrong - which is why this is in place. Defaults to True.
            bounciness (float, optional): How bouncy this object is. 1 = rebounds perfectly, <1 = eventually will stop, >1 = will bounce more each time. Defaults to 0.7.

        Raises:
            ValueError: When you have a polygon with <3 points.
        """
        super().__init__(bounciness)
        if len(points) < 3 and errorOnLT3:
            raise ValueError(
                f'Cannot have a Polygon with less than 3 points! Found: {len(points)} points!'
            )
        self.points = list(points)
    
    @property
    def x(self):
        """One of this object's points' x value. Changing this will move the other points by the difference!"""
        return min([i[0] for i in self.points])
    @x.setter
    def x(self, new):
        diff = new - self.x
        self.points = [[i[0]+diff, i[1]] for i in self.points]
    @property
    def y(self):
        """One of this object's points' y value. Changing this will move the other points by the difference!"""
        return min([i[1] for i in self.points])
    @y.setter
    def y(self, new):
        diff = new - self.y
        self.points = [[i[0], i[1]+diff] for i in self.points]
    
    def rect(self) -> Iterable[Number]:
        """
        Returns the rectangle bounding box surrounding this polygon.

        Returns:
            Iterable[Number]: (min x, min y, max x, max y)
        """
        return min([i[0] for i in self.points]), min([i[1] for i in self.points]), max([i[0] for i in self.points]), max([i[1] for i in self.points])
    
    def area(self) -> Number:
        """
        Gets the area of the shape.

        Returns:
            Number: The area of the shape
        """
        return abs(sum(
            (self.points[i][0] * self.points[i+1][1] - self.points[i+1][0] * self.points[i][1])
            for i in range(len(self.points)-1)
        ) + (self.points[len(self.points)-1][0] * self.points[0][1] - self.points[0][0] * self.points[len(self.points)-1][1])) / 2
    
    def _collides(self, othershape: Shape) -> bool:
        if not self.check_rects(othershape):
            return False
        if checkShpType(othershape, ShpTyps.Point):
            ps = self.points
            c = False
            j = len(ps) - 1
            for i in range(len(ps)):
                if ((ps[i][1] > othershape.y) != (ps[j][1] > othershape.y)) and \
                (othershape.x < (ps[j][0] - ps[i][0]) * (othershape.y - ps[i][1]) / (ps[j][1] - ps[i][1]) + ps[i][0]):
                    c = not c
                j = i
            return c
        if checkShpType(othershape, ShpTyps.Line):
            for li in self.toLines():
                if li.collides(othershape):
                    return True
            if self._collides(Point(*othershape.p1)) or self._collides(Point(*othershape.p2)):
                return True
            return False
        if checkShpType(othershape, ShpTyps.Circle):
            if self._collides(Point(othershape.x, othershape.y)):
                return True
            for li in self.toLines():
                if li.collides(othershape):
                    return True
            return False
        if checkShpType(othershape, ShpTyps.Arc):
            if any(self._collides(Point(*i)) for i in othershape.endPoints()):
                return True
            for i in self.toLines():
                if othershape.collides(i):
                    return True
            return False
        if checkShpType(othershape, ShpTyps.Rect, ShpTyps.RotRect):
            for li in self.toLines():
                if li.collides(othershape):
                    return True
            return othershape.collides(Point(self.points[0][0], self.points[0][1])) or self.collides(Point(othershape.x, othershape.y))
        if checkShpType(othershape, ShpTyps.Polygon):
            for li in self.toLines():
                if li.collides(othershape):
                    return True
            return othershape.collides(Point(self.points[0][0], self.points[0][1])) or self.collides(Point(othershape.points[0][0], othershape.points[0][1]))
        return othershape._collides(self)

    def toLines(self) -> Iterable[Line]:
        """
        Returns:
            Iterable[Line]: Get a list of all the Lines that make up this object.
        """
        return [
            Line(self.points[i], self.points[i+1])
            for i in range(len(self.points)-1)
        ] + [Line(self.points[len(self.points)-1], self.points[0])]
    
    def toPoints(self) -> Iterable[pointLike]:
        """
        Returns:
            Iterable[pointLike]: Get a list of all the Points that make up this object.
        """
        return [list(i) for i in self.points]
    
    def copy(self) -> 'Polygon':
        """
        And then he lifted his arms and said, 'LET THERE BE ANOTHER!'
        """
        return Polygon(*self.points, errorOnLT3=False, bounciness=self.bounciness)
    
    def __setitem__(self, item: int, new: pointLike) -> None:
        self.points[item] = new
    
    def __str__(self):
        return f'<Polygon with points {self.points}>'


# TODO: Options for having func(a, b, c) OR func([a, b, c])
# TODO: Area and distance_to for all shapes
# TODO: Split functions up into smaller bits and have more sharing of functions (especially with the handleCollisions)
# TODO: Ovals, ovaloids and arcs (Ellipse & capsule)
# TODO: Can also input pointlike, linelike (2 points) and polygon-like iterables into all functions to reduce conversion

# TODO: Improve calculations - 1. with matricies and dot product 2. by not stuffing up angle calculations (0 degrees is right, so fix the weird +- 90 degree conversions I've been doing) 3. expanding the rotate funcs to their base code

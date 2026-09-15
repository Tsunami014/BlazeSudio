from base import Finish, Check, AssertEqual, CompareTimes

def testCollisions():
    from BlazeSudio import collisions

    # Base rotate functions
    # If these fail there is a big issue
    AssertEqual('Basic Rotate 1: `rotate` works', ['x', 'y'],
                collisions.rotate([0, 0], [123, 456], 127.001), collisions.rotateBy0([123, 456], 127.001))
    AssertEqual('Basic Rotate 2: `rotate` around (0,0) vs `rotateBy0`', ['x', 'y'],
                collisions.rotate([1, 0], [1, -1], 90), (2, 0))

    # Test points
    def testPoint(testName, inp, invel, shapeCollisions, expected1, expected2):
        outp, outvel = collisions.Point(*inp).handleCollisionsVel(invel, collisions.Shapes(*shapeCollisions))
        Check(testName,
            ['x', 'y', 'accelx', 'accely'],
            [*inp, *invel],
            [*outp, *outvel],
            [*expected1, *expected2],
            lambda li: f'({li[0]}, {li[1]}), [{li[2]}, {li[3]}]'
        )

    testPoint('Point 1: Perfect rebound',
            (2, 0), [0, 2], [collisions.Rect(0, 1, 4, 4, 1)],
            (2, 0), # It rebounded perfectly and now is exactly where it started
            (0, -2)) # It is now going the opposite direction
    # . = current pos, N = new pos
    #  .
    #+--+
    #| N|
    #|  |
    #+--+
    testPoint('Point 2: Perfect rebound 2 - side',
            (0, 2), [2, 0], [collisions.Rect(1, 0, 4, 4, 1)],
            (0, 2), # It rebounded perfectly and now is exactly where it started
            (-2, 0)) # It is now going the opposite direction
    # . = current pos, N = new pos
    # +--+
    # |  |
    #.|N |
    # +--+
    testPoint('Point 3: v shape',
            (0, 0), [2, 2], [collisions.Rect(0, 1, 4, 4, 1)],
            (2, 0), # It rebounded like a v shape
            (2, -2))
    # . = current pos, N = new pos
    #.
    #+--+
    #| N|
    #|  |
    #+--+

    # Test lines
    def testLine(testName, line, accel, shapes, expectedp1, expectedp2, expectedaccel, expectedtype):
        outLine, outvel, v = collisions.Line(*line).handleCollisionsVel(accel, collisions.Shapes(*shapes), verbose=True)
        Check(testName,
              ['p1x', 'p1y', 'p2x', 'p2y', 'accelx', 'accely', 'type'],
              [*line[0], *line[1], *accel, 'N/A'],
              [*outLine[0], *outLine[1], *outvel, v[0]],
              [*expectedp1, *expectedp2, *expectedaccel, expectedtype],
              lambda li: f'({li[0]}, {li[1]}), ({li[2]}, {li[3]}), ({li[4]}, {li[5]}), {li[6]}'
        )

    # Types of collisions:
    # 0: Point off point collision
    # 1: Point off line collision
    # 2: Line off point collision
    # 3: Line off line collision

    testLine('Line 1: Basic point off line',
             ((1, 0), (2, -1)), [0, 3], collisions.Shapes(collisions.Rect(0, 1, 4, 4, 1)),
             (1, -1), (2, -2), (0, -3), 1)
    # /
    #+--+
    #|  |
    #|  |
    #+--+

    testLine('Line 2: Basic point off line 2: points reversed',
             ((2, -1), (1, 0)), [0, 3], collisions.Shapes(collisions.Rect(0, 1, 4, 4, 1)),
             (1, -1), (2, -2), (0, -3), 1)
    # /
    #+--+
    #|  |
    #|  |
    #+--+

    testLine('Line 3: Basic point off line 3: closer to rect',
             ((1, 0.9), (2, 0)), [0, 0.3], collisions.Shapes(collisions.Rect(0, 1, 4, 4, 1)),
             (1, 0.8), (2, -0.1), (0, -0.3), 1)
    # /
    #+--+
    #|  |
    #|  |
    #+--+

    testLine('Line 4: Basic point off line 4: further from rect',
             ((2, -3), (4, -4)), [0, 6], collisions.Shapes(collisions.Rect(0, 1, 4, 4, 1)),
             (2, -1), (4, -2), (0, -6), 1)
    # /
    #+--+
    #|  |
    #|  |
    #+--+

    testLine('Line 5: V shape bounce point off line',
             ((0, 0), (1, -1)), [2, 2], collisions.Shapes(collisions.Rect(0, 1, 4, 4, 1)),
             (2, 0), (3, -1), (2, -2), 1)
    #/v/
    #+--+
    #|  |
    #|  |
    #+--+

    testLine('Line 6: Non-basic copied from a (hopefully previously) incorrect scenario in demos.py',
             ((620.52, 584), (670.52, 684)), [-3.52, 0], collisions.Shapes(collisions.Rect(520, 547, 100, 100, 1)),
             (623, 584), (673, 684), (3.52, 0), 1)
    #+--+
    #|  |
    #|  |/
    #+--+

    testLine('Line 7: Line bounce off another paralell line',
             ((0, 1), (1, 0)), [0, 2], collisions.Shapes(collisions.Line((0, 2), (1, 1), 1)),
             (-1, 2), (0, 1), (-2, 0), 3)
    #/
    #/

    testLine('Line 8: Line bounce off rect corner',
             ((0, 1), (1, 0)), [1, 1], collisions.Shapes(collisions.Rect(1, 1, 4, 4, 1)),
             (0, 1), (1, 0), (-1, -1), 2)
    #/+--+
    # |  |
    # |  |
    # +--+

    testLine('Line 9: Line v shape off circle exact',
             ((0, 0), (1.5, 0)), [1, 1], collisions.Shapes(collisions.Circle(2, 2, 1, 1)),
             (1, 1), (2.5, 1), (-1, -1), 3)
    #─-
    # O

    # Test circles
    def testCircles(testName, inps, vel, collShps, expectedpos, expectedvel):
        outcirc, outvel = collisions.Circle(*inps).handleCollisionsVel(vel, collisions.Shapes(*collShps))
        Check(testName,
            ['x', 'y', 'radius', 'accelx', 'accely'],
            [*inps, *vel],
            [*outcirc, *outvel],
            [*expectedpos, inps[2], *expectedvel],
            lambda li: f'({li[0]}, {li[1]}, {li[2]}), [{li[3]}, {li[4]}]'
        )

    testCircles('Circle 1: Rebound top',
                (2, 0, 1), [0, 2], [collisions.Rect(0, 0, 4, 4, 1)],
                (2, 0),
                (0, -3)) # It is now going the opposite direction
    # o = current pos, N = new pos
    #  o
    #+--+
    #| N|
    #|  |
    #+--+
    testCircles('Circle 2: Rebound side',
                (0, 2, 1), [2, 0], [collisions.Rect(1, 0, 4, 4, 1)],
                (0, 2), # It rebounded perfectly and now is exactly where it started
                (-2, 0)) # It is now going the opposite direction
    # o = current pos, N = new pos
    # +--+
    # |  |
    #o|N |
    # +--+
    testCircles('Circle 3: v shape',
                (0, 0, 1), [2, 2], [collisions.Rect(0, 1, 4, 4, 1)],
                (2, 0), # It rebounded like a v shape
                (2, -2))
    # o = current pos, N = new pos
    #o
    #+--+
    #| N|
    #|  |
    #+--+

    # TIMING
    shp1 = collisions.RotatedRect(0, 0, 1, 1, 45)
    shp2 = collisions.Polygon((0.5, 0), (1, 0.5), (0.5, 1), (0, 0.5))
    CompareTimes('Timing 1: rotated rect vs polygon',
                 'Rotated rect handle collisions', shp1.handleCollisionsVel,
                 'Polygon handle collisions', shp2.handleCollisionsVel,
                 [1, 1], collisions.Shapes(collisions.Rect(-99, 0, 10, 19))
    )


def testAll():
    print('COLLISIONS TESTS')
    testCollisions()
    Finish()

if __name__ == '__main__':
    import sys
    import os
    sys.path.append(os.path.abspath(__file__+"/../.."))
    testAll()

"""Collisions demo [collisions]"""

def main():
    from BlazeSudio import collisions
    from BlazeSudio.graphicsCore import Core, Ix, AvgClock, Col, Op, Font
    import math
    header_opts = ['point', 'line', 'arc', 'circle', 'rect', 'rotated rect', 'polygon', 'eraser', 'combiner', 'help']
    types = [collisions.Point, collisions.Line, collisions.Arc, collisions.Circle, collisions.Rect, collisions.RotatedRect, collisions.Polygon, collisions.NoShape]
    rbw = Col.Rainbow()
    cols = [next(rbw) for _ in range(len(header_opts))]

    FONT = Font.SysFonts.default()
    header_sze = FONT.lineheight+20
    MOD_SPEED = 1
    SPEED = 0.08
    gravity_amnt = 0.03
    friction_amnt = 0.001
    typ = 0
    curObj: collisions.Shape = collisions.Point(0, 0)
    objs = collisions.Shapes()
    dir = [0, 0, 0]
    combineTyp = 0
    pos = [0, 0]
    vel = [0, 0]
    combineFs = {
        'CollsUnion': collisions.Combine.union,
        'ShapelyUnion': collisions.shapely.shapelyUnion,
        'BoundingBox': collisions.Combine.boundingBox,
        'CombineRects': collisions.Combine.combineRects,
        'PointsToShape': collisions.Combine.pointsToShape,
        'PointsToPoly': collisions.shapely.pointsToPoly
    }
    highlightTyps = [
        (collisions.Line, collisions.ClosedShape),
        (collisions.Shape),
        (collisions.Shape),
        (collisions.Rect),
        (collisions.Point),
        (collisions.Point)
    ]
    combineCache = [None, None]

    def findCombinedOutput():
        nonlocal combineCache
        toCombineObjs = [o for o in objs if isinstance(o, highlightTyps[combineTyp]) and o.collides(curObj)]
        cacheCheck = (toCombineObjs, combineTyp)
        if combineCache[0] == cacheCheck:
            return combineCache[1]
        else:
            combined = combineFs[list(combineFs.keys())[combineTyp]](*toCombineObjs)
            ret = (combined, toCombineObjs)
            combineCache = [cacheCheck, ret]
            return ret

    def drawObj(obj, t, col):
        out = collisions.drawShape(obj, col, 8)
        if t == 8: # As well as drawing the point, outline the shapes to be combined
            combined, objsToCombine = findCombinedOutput()
            if isinstance(combined, collisions.Shape):
                combined = [combined]
            for o in objsToCombine:
                out += drawObj(o, types.index(type(o)), (255, 110, 60))
            for o in combined:
                out += drawObj(o, types.index(type(o)), (244, 194, 194, 200))
        if t == 7:
            col = (255, 255, 255)
            # Outline shapes to be deleted
            for o in objs:
                if curObj.collides(o):
                    out +=  drawObj(o, types.index(type(o)), (255, 110, 60))
        return out

    def moveCurObj(curObj):
        if typ == 1:
            curObj.p1 = pos
            curObj.p2 = (curObj.p1[0]+dir[0], curObj.p1[1]+dir[1])
        elif typ == 6:
            moveAll = Ix.Keys['.'] or playMode
            if isinstance(curObj, collisions.Point):
                curObj.x, curObj.y = pos
            elif isinstance(curObj, collisions.Line):
                if moveAll:
                    curObj.p1 = [curObj.p1[0]-curObj.p2[0]+pos[0], curObj.p1[1]-curObj.p2[1]+pos[1]]
                curObj.p2 = pos
            else:
                if moveAll:
                    diff = (curObj.points[-1][0]-pos[0], curObj.points[-1][1]-pos[1])
                    curObj.points = [(p[0]-diff[0], p[1]-diff[1]) for p in curObj.points[:-1]] + [pos]
                else:
                    curObj.points[-1] = pos
        else:
            curObj.x, curObj.y = pos
            if typ in (2, 3):
                curObj.r = dir[1]
            elif typ in (4, 5, 7, 8):
                curObj.w, curObj.h = dir[0], dir[1]
                if typ == 5:
                    curObj.rot = dir[2]
            if typ == 2:
                dir[0], dir[2] = dir[0] % 360, dir[2] % 360
                curObj.startAng, curObj.endAng = dir[0], dir[2]
        return curObj

    clock = AvgClock()
    while Ix.handleBasic():
        playMode = Ix.Keys.mAlt
        if not playMode:
            for ev in Ix.loopEvs():
                if (kev := Ix.KeyEvent(ev, Ix.EvTyp.KeyDown)):
                    if kev.scode == 'Space':
                        if typ == 7:
                            for i in objs.copy_leave_shapes():
                                if i.collides(curObj):
                                    objs.remove_shape(i)
                        elif typ == 8:
                            new, toRemove = findCombinedOutput()
                            objs.remove_shapes(*toRemove)
                            objs.add_shapes(*new)
                        else:
                            objs.add_shape(curObj)
                            if typ == 6:
                                curObj = curObj = collisions.Point(*Ix.Mouse.pos)
                            else:
                                curObj = curObj.copy()
                    elif kev.scode == ',' and typ == 6:
                        if isinstance(curObj, collisions.Point):
                            curObj = collisions.Line(curObj.getTuple(), Ix.Mouse.pos)
                        elif isinstance(curObj, collisions.Line):
                            curObj = collisions.Polygon(curObj.p1, curObj.p2, Ix.Mouse.pos)
                        else:
                            curObj.points += [Ix.Mouse.pos]
                    elif kev.scode == ',' and typ == 8:
                        combineTyp = (combineTyp + 1) % len(combineFs)
                    elif kev.scode == '.' and typ == 8:
                        combineTyp = (combineTyp - 1) % len(combineFs)
                    elif kev.scode == '-':
                        curObj.bounciness = max(0.1, round(curObj.bounciness-0.05, 3))
                    elif kev.scode == '=':
                        curObj.bounciness = min(1.5, round(curObj.bounciness+0.05, 3))
                    elif kev.scode == 'R':
                        objs = collisions.Shapes()
                    elif kev.scode == 'W':
                        dir[1] -= 5
                    elif kev.scode == 'S':
                        dir[1] += 5
                    elif kev.scode == 'A':
                        dir[0] -= 5
                    elif kev.scode == 'D':
                        dir[0] += 5
                elif (mev := Ix.MouseEvent(ev, Ix.EvTyp.MouseDown)):
                    # Get the header_opts that got clicked, if any
                    if mev.y < header_sze:
                        oldtyp = typ
                        typ = mev.x//(Core.width//len(header_opts))
                        if typ == 0:
                            curObj = collisions.Point(*mev.pos)
                        elif typ == 1:
                            curObj = collisions.Line((0, 0), (10, 10))
                            dir = [50, 100, 0]
                        elif typ == 2:
                            curObj = collisions.Arc(*mev.pos, 100, -135, -45)
                            dir = [-135, 100, -45]
                        elif typ == 3:
                            curObj = collisions.Circle(*mev.pos, 100)
                            dir = [0, 100, 0]
                        elif typ == 4:
                            curObj = collisions.Rect(*mev.pos, 100, 100)
                            dir = [100, 100, 0]
                        elif typ == 5:
                            curObj = collisions.RotatedRect(*mev.pos, 100, 100, 45)
                            dir = [100, 100, 45]
                        elif typ == 6:
                            curObj = collisions.Point(*mev.pos)
                        elif typ == 7:
                            curObj = collisions.Rect(*mev.pos, 0, 0)
                            dir = [0, 0, 0]
                        elif typ == 8:
                            curObj = collisions.Rect(*mev.pos, 0, 0)
                            dir = [0, 0, 0]
                        else: # Last item in list - help menu
                            run2 = True
                            prevWid = None
                            while run2 and Ix.handleBasic():
                                if prevWid != Core.width:
                                    prevWid = Core.width
                                    Core(FONT.render("""How to use:
Click on one of the options at the top to change your tool. Pressing space adds it to the board (or applies some function to existing objects).\
The up, down, left and right arrow keys as well as comma and full stop do stuff with some of them too. When not holding alt to be in play mode, wsad does the same as the arrow keys but is more precise.
Holding '[' and ']' changes the bounciness of the object, and '-' and '=' are to fine-tune.
Holding shift in this mode shows the normals, and holding control shows the closest points to the object!
And holding alt allows you to test the movement physics. Holding shift and alt makes the movement physics have gravity, and holding ctrl reverses that gravity! Holding 'L' makes you have no friction. \
And holding '/' while holding shift will... well... I'll let you find that out for yourself.
And pressing 'r' will reset everything without warning.

Press any key/mouse to close this window""", Col.Black, prevWid))
                                    Core.rend()
                                for ev in Ix.loopEvs():
                                    if Ix.MouseEvent(ev, Ix.EvTyp.MouseDown) or Ix.KeyEvent(ev, Ix.EvTyp.KeyDown):
                                        run2 = False
                                        break
                                clock.tick(60)
                            typ = oldtyp

            if Ix.Keys["up"]:
                dir[1] -= MOD_SPEED
            if Ix.Keys["down"]:
                dir[1] += MOD_SPEED
            if Ix.Keys["left"]:
                dir[0] -= MOD_SPEED
            if Ix.Keys["right"]:
                dir[0] += MOD_SPEED
            if Ix.Keys[","]:
                dir[2] -= MOD_SPEED
            if Ix.Keys["."]:
                dir[2] += MOD_SPEED

        if Ix.Keys["w"]:
            vel[1] -= SPEED
        if Ix.Keys["s"]:
            vel[1] += SPEED
        if Ix.Keys["a"]:
            vel[0] -= SPEED
        if Ix.Keys["d"]:
            vel[0] += SPEED

        if Ix.Keys["["]:
            curObj.bounciness = max(0.1, round(curObj.bounciness-0.05, 3))
        if Ix.Keys["]"]:
            curObj.bounciness = min(1.5, round(curObj.bounciness+0.05, 3))

        if (not playMode) and objs.collides(curObj):
            if curObj.isContaining(objs):
                ops = Op.Fill(Col.Blue)
            else:
                ops = Op.Fill(Col.Red)
        else:
            ops = Op.Fill(Col.Black)
        ops += Op.Draw.Rect(0, 0, Core.width, header_sze, 0, Col.White)
        # Split it up into equal segments and put the text header_opts[i] in the middle of each segment
        eachwid = Core.width//len(header_opts)
        for i in range(len(header_opts)):
            ops += Op.Draw.Line(
                (i*eachwid, 0), (i*eachwid, header_sze),
                2, Col.Black)
            ops += FONT.render(header_opts[i], Col.Black) @ (i*eachwid+10, 10)

        if playMode:
            if Ix.Keys.mShift:
                if Ix.Keys['/']:
                    cpoints = objs.closestPointTo(curObj) # [(i, i.closestPointTo(curObj)) for i in objs]
                    if cpoints:
                        # Find the point on the unit circle * 0.2 that is closest to the object
                        angle = math.atan2(curObj.y-cpoints[1], curObj.x-cpoints[0])
                        gravity = [-gravity_amnt*math.cos(angle), -gravity_amnt*math.sin(angle)]
                    else:
                        gravity = [0, 0]
                elif Ix.Keys.mCtrl:
                    gravity = [0, -gravity_amnt]
                else:
                    gravity = [0, gravity_amnt]
            else:
                gravity = [0, 0]
            vel = [vel[0] + gravity[0], vel[1] + gravity[1]]
            vellLimits = [10, 10]
            vel = [min(max(vel[0], -vellLimits[0]), vellLimits[0]), min(max(vel[1], -vellLimits[1]), vellLimits[1])]
            if not Ix.Keys['l']:
                friction = [friction_amnt, friction_amnt]
            else:
                friction = [0, 0]
            def fric_eff(x, fric):
                if x < -fric:
                    return x + fric
                if x > fric:
                    return x - fric
                return 0
            vel = [fric_eff(vel[0], friction[0]), fric_eff(vel[1], friction[1])]
            _, vel = curObj.handleCollisionsVel(vel, objs)

        else:
            pos = Ix.Mouse.pos
            vel = [0, 0]
            curObj = moveCurObj(curObj)

        for i in objs:
            ops += drawObj(i, types.index(type(i)), Col.Green)
        ops += drawObj(curObj, typ, cols[typ])

        if not playMode:
            for i in objs.whereCollides(curObj):
                ops += Op.Draw.Circle(i, 8, 0, Col.Purple)

            if Ix.Keys.mShift:
                mpos = Ix.Mouse.pos
                for o in objs:
                    if Ix.Keys.mCtrl:
                        cs = [o.closestPointTo(curObj)]
                    else:
                        cs = o.whereCollides(curObj)
                    for i in cs:
                        ops += Op.Draw.Line(i, collisions.rotate(i, [i[0], i[1]-50], o.tangent(i, [i[0]-mpos[0], i[1]-mpos[1]])-90),
                            8, Col.Indigo)
            if Ix.Keys.mCtrl:
                for o in objs:
                    p = o.closestPointTo(curObj)
                    ops += Op.Draw.Circle(p, 8, 0, (Col.Yellow if o.isCorner(p) else Col.Orange))
            for p in curObj.toLines():
                ops += Op.Draw.Line(p[0], p[1], 6, (10, 50, 50, 100))
            for p in curObj.toPoints():
                ops += Op.Draw.Circle(p, 4, 0, Col.White)
            if typ < 7:
                #win.blit(font.render(f'Bounciness: {curObj.bounciness}', 1, (255, 255, 255)), (0, header_sze+2))
                pass
        if typ == 8:
            #win.blit(font.render(list(combineFs.keys())[combineTyp], 1, (255, 255, 255)), (0, header_sze+2))
            pass
        Core(ops)
        Core.rend()
        clock.tick(60)
    Core.Quit()

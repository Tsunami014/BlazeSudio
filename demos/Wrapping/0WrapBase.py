"""Basic wrapping [image]"""
def main():
    import time
    import BlazeSudio.collisions as colls
    from BlazeSudio.utils.wrap import WrapJoints, FindBounds
    from BlazeSudio.graphicsCore import Core, Ix, Clock, Col, Op, Draw, Font

    Core.resize()
    clk = Clock()

    SHAPE = [(0, None), (100, None)]
    POLYS = None
    conns = {
        '|': 0,
        '-': 90,
        '/': -45,
        '\\': 45,
    }

    heldSegment = None
    selectedSegment = None
    movingMode = False
    extratxt = ""
    while Ix.handleBasic():
        newMM = Ix.Keys.mAlt
        if newMM and not movingMode:
            try:
                b4 = time.time()
                js, rad = WrapJoints(
                    [(i[0],0) for i in SHAPE],
                    [i[1] for i in SHAPE],
                    return_radius=True)
                POLYS = (js, *FindBounds(rad, js, 100))
                now = time.time()
                extratxt = f"Success! Took {round(now-b4, 2)} secs."
            except Exception as e:
                extratxt = f"{type(e)}: {e}"
        if not newMM:
            extratxt = ""
            POLYS = None
        movingMode = newMM

        if POLYS is None:
            xoffs = (Core.width-SHAPE[-1][0]-SHAPE[0][0])/2
            yoffs = Core.height/2
        else:
            xs, ys = zip(*POLYS[0])
            xoffs = (Core.width-max(xs)-min(xs))/2
            yoffs = (Core.height-max(ys)-min(ys))/2

        selectedJoint = (None, None)
        if not movingMode:
            mp = Ix.Mouse.pos
            for idx in range(len(SHAPE)):
                i = SHAPE[idx]
                if POLYS is None:
                    d = (i[0]+xoffs-mp[0])**2+(yoffs-mp[1])**2
                else:
                    p = POLYS[0][idx]
                    d = (p[0]-mp[0]+xoffs)**2+(p[1]-mp[1]+xoffs)**2
                if d <= 10*10:
                    selectedJoint = (idx, i)
                    break

        boxes = len(conns)
        gap = 10
        boxSze = 30

        if selectedSegment is not None:
            h = boxSze+gap*2
            w = (boxSze+gap)*boxes+gap
            x, y = (selectedSegment[0][0][0]+selectedSegment[0][1][0]-w)/2, min(selectedSegment[0][0][1], selectedSegment[0][1][1])-h-gap*3

            SelectedR = colls.Rect(x, y, w, h)

        if not movingMode:
            for event in Ix.loopEvs():
                if kev := Ix.KeyEvent(event, Ix.EvTyp.KeyDown):
                    if selectedJoint[0] is None and kev.key == 'Space':
                        SHAPE.append((Ix.Mouse.x-xoffs, None))
                        SHAPE.sort()
                    elif kev.key == 'R':
                        SHAPE = [(0,None), (100,None)]
                        heldSegment = None
                        selectedJoint = (None, None)
                        selectedSegment = None
                elif (mev := Ix.MouseEvent(event, Ix.EvTyp.MouseDown)) and mev.button == 1:
                    heldSegment = selectedJoint[0]

                    mp = colls.Point(*mev.pos)
                    if selectedSegment is None or not SelectedR.collides(mp):
                        selectedSegment = None
                        idx = 0
                        for i in range(len(SHAPE)-1):
                            seg = colls.Line((SHAPE[i][0]+xoffs, yoffs), (SHAPE[i+1][0]+xoffs, yoffs))
                            p = seg.closestPointTo(mp)
                            if (p[0]-mev.x)**2+(p[1]-mev.y)**2 <= 5**2:
                                selectedSegment = (seg, idx)
                                break
                            idx += 1
                    else:
                        for i in range(boxes):
                            r = colls.Rect(x+(boxSze+gap)*i+gap, y+gap, boxSze, boxSze)
                            if r.collides(mp):
                                val = list(conns.values())[i]
                                idx = selectedSegment[1]
                                SHAPE[idx] = (SHAPE[idx][0], val)
                                break

            if Ix.Keys['s'] and (selectedJoint[0] is None):
                SHAPE.append((Ix.Mouse.x-xoffs, None))
                SHAPE.sort()

        if heldSegment is not None and (not Ix.Mouse.left):
            heldSegment = None

        ops = Op.Fill(Col.Black)

        if movingMode:
            selectedSegment = None
            heldSegment = None
        elif heldSegment is not None:
            selectedSegment = None
            newx = Ix.Mouse.x-xoffs
            SHAPE[heldSegment] = (newx, SHAPE[heldSegment][1])
            nxrnd = round(newx,6)
            diff = 0
            for idx, s in enumerate(SHAPE.copy()):
                if idx != heldSegment and round(s[0],6) == nxrnd:
                    SHAPE.pop(idx - diff)
                    diff += 1
            SHAPE.sort()
            heldSegment = None
            for idx, s in enumerate(SHAPE):
                if round(s[0],6) == nxrnd:
                    heldSegment = idx
                    break

        if selectedSegment is not None:
            ops += Draw.Line(selectedSegment[0].toPoints(), 15, Col.Orange)

        joints = [(p[0]+xoffs, p[1]+yoffs) for p in POLYS[0]] if POLYS is not None else \
            [(s[0]+xoffs, yoffs) for s in SHAPE]
        for i in range(len(SHAPE)-1):
            if SHAPE[i][1] is not None:
                col = Col.Indigo
            else:
                col = Col.White
            ops += Draw.Line(joints[i], joints[i+1], 10, col)
        idx = 0
        for idx, j in enumerate(joints):
            if idx == selectedJoint[1]:
                ops += Draw.Circle(j, 5, 0, Col.Red)
            elif idx in (0, len(joints)-1):
                ops += Draw.Circle(j, 5, 0, Col.Purple)
            else:
                ops += Draw.Circle(j, 5, 0, Col.Blue)
            idx += 1

        if selectedSegment is not None:
            h = boxSze+gap*2
            w = (boxSze+gap)*boxes+gap
            x, y = (selectedSegment[0][0][0]+selectedSegment[0][1][0]-w)/2, min(selectedSegment[0][0][1], selectedSegment[0][1][1])-h-gap*3
            ops += Draw.Rect(x, y, w, h, 0, Col.Grey, roundness=4)
            vals = list(conns.values())
            f = Font.Font(None, boxSze)
            for i in range(boxes):
                r = colls.Rect(x+(boxSze+gap)*i+gap, y+gap, boxSze, boxSze)
                mp = colls.Point(*Ix.Mouse.pos)
                if vals[i] == SHAPE[selectedSegment[1]][1]:
                    if r.collides(mp):
                        col = Col.Purple
                    else:
                        col = Col.Blue
                else:
                    if r.collides(mp):
                        col = Col.Yellow
                    else:
                        col = Col.White
                ops += Draw.Rect(r.x, r.y, r.w, r.h, 0, col, roundness=4)
                ops += f.render(list(conns.keys())[i], Col.Black, **Op.Anchors.Middle) @ (r.x+r.w/2, r.y+r.h/2)

        if movingMode and POLYS is not None:
            # Outer Polygon
            ops += Draw.Polygon(
                [(p[0]+xoffs, p[1]+yoffs) for p in POLYS[1]],
                3, Col.Grey)

            # Inner Shapes
            for poly in POLYS[2]:
                ops += Draw.Line(
                    (poly[0][0]+xoffs, poly[0][1]+yoffs),
                    (poly[1][0]+xoffs, poly[1][1]+yoffs),
                    3, Col.Grey)

        ops += Font.Font().render("""
Space to place one, s to place many
Can drag individual points
Click on segments
Hold Alt to execute
"""[1:-1]+f'\n{round(clk.get_fps(),1)} FPS\n'+extratxt, Col.White)
        Core(ops).rend()
        clk.tick()
    Core.Quit()

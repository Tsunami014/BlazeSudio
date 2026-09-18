"""Basic wrapping [image]"""
def main():
    from BlazeSudio.collisions import Point, Rect
    from BlazeSudio.utils.wrap import makeShape
    from BlazeSudio.graphicsCore import Core, Ix, Clock, Col, Op, Draw, Font

    Core.resize()
    clk = Clock()

    main = makeShape.MakeShape(100)
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
                main.makeShape()
                extratxt = "Success!"
            except Exception as e:
                extratxt = f"{type(e)}: {e}"
        if not newMM:
            extratxt = ""
        movingMode = newMM

        selectedJoint = (None, None)
        if not movingMode:
            mp = Ix.Mouse.pos
            for idx in range(len(main.joints)):
                i = main.joints[idx]
                if (i[0]-mp[0])**2+(i[1]-mp[1])**2 <= 5**2:
                    selectedJoint = (idx, i)
                    break

        boxes = len(conns)
        gap = 10
        boxSze = 30

        if selectedSegment is not None:
            h = boxSze+gap*2
            w = (boxSze+gap)*boxes+gap
            x, y = (selectedSegment[0][0][0]+selectedSegment[0][1][0]-w)/2, min(selectedSegment[0][0][1], selectedSegment[0][1][1])-h-gap*3

            SelectedR = Rect(x, y, w, h)

        for event in Ix.loopEvs():
            if kev := Ix.KeyEvent(event, Ix.EvTyp.KeyDown):
                if kev.key == 'Space':
                    if (not movingMode) and (selectedJoint[0] is None):
                        main.insert_straight(Ix.Mouse.x)
                elif kev.key == 'R':
                    main = makeShape.MakeShape(100)
                    heldSegment = None
                    selectedJoint = (None, None)
                    selectedSegment = None
            elif (mev := Ix.MouseEvent(event, Ix.EvTyp.MouseDown)) and mev.button == 1:
                if not movingMode:
                    heldSegment = selectedJoint[0]

                    mp = Point(*mev.pos)
                    if selectedSegment is None or not SelectedR.collides(mp):
                        selectedSegment = None
                        idx = 0
                        for seg in main.collSegments:
                            p = seg.closestPointTo(mp)
                            if (p[0]-mev.x)**2+(p[1]-mev.y)**2 <= 5**2:
                                selectedSegment = (seg, idx)
                                break
                            idx += 1
                    else:
                        for i in range(boxes):
                            r = Rect(x+(boxSze+gap)*i+gap, y+gap, boxSze, boxSze)
                            if r.collides(mp):
                                val = list(conns.values())[i]
                                main.setAngs[selectedSegment[1]] = val
                                break

        if Ix.Keys['s']:
            if (not movingMode) and (selectedJoint[0] is None):
                main.insert_straight(Ix.Mouse.x)

        if heldSegment is not None and (not Ix.Mouse.left):
            heldSegment = None

        ops = Op.Fill(Col.Black)

        y = Core.height/2
        x = (Core.width+main.width)/2

        if movingMode:
            selectedSegment = None
            heldSegment = None
            if not Ix.Keys.mShift:
                main.recentre(*Ix.Mouse.pos)
        else:
            if heldSegment is not None:
                selectedSegment = None
                newx = Ix.Mouse.x
                if heldSegment > 0:
                    newx = min(newx, main.joints[heldSegment-1][0])
                if heldSegment < len(main.joints)-1:
                    newx = max(newx, main.joints[heldSegment+1][0])
                if [round(j[0],6) for j in main.joints].count(round(newx,6)) > 1:
                    main.delete(heldSegment)
                    heldSegment = None
                else:
                    main.joints[heldSegment] = (newx, main.joints[heldSegment][1])
                main.recalculate_dists()
            else:
                main.joints[0] = (x, y)
                main.straighten()

        if selectedSegment is not None:
            ops += Draw.Line(selectedSegment[0].toPoints(), 15, Col.Orange)

        segs = main.segments
        for i in range(len(segs)):
            if main.setAngs[i] is not None:
                col = Col.Indigo
            else:
                col = Col.White
            ops += Draw.Line(segs[i], 10, col)
        idx = 0
        for j in main.joints:
            if j == selectedJoint[1]:
                ops += Draw.Circle(j, 5, 0, Col.Red)
            elif idx in (0, len(main.joints)-1):
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
                r = Rect(x+(boxSze+gap)*i+gap, y+gap, boxSze, boxSze)
                mp = Point(*Ix.Mouse.pos)
                if vals[i] == main.setAngs[selectedSegment[1]]:
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

        if movingMode:
            polys = main.generateBounds(100, True, False, True)

            # Outer Polygon
            ps = list(polys[0])
            for i in range(len(ps)-1):
                ops += Draw.Line(ps[i], ps[i+1], 3, Col.Grey)

            # Inner Shapes
            for i in polys[2]:
                ops += Draw.Line(i[0], i[1], 3, Col.Grey)

        ops += Font.Font().render(f'{round(clk.get_fps(),1)} FPS\n'+extratxt, Col.White)
        Core(ops).rend()
        clk.tick()
    Core.Quit()

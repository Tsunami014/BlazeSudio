"""Basic wrapping [image]"""
def main():
    from BlazeSudio.collisions import Point
    from BlazeSudio.utils.wrap import makeShape
    import pygame
    import sys
    pygame.init()

    win = pygame.display.set_mode()
    pygame.display.toggle_fullscreen()

    main = makeShape.MakeShape(100)

    conns = {
        '|': 0,
        '-': 90,
        '/': -45,
        '\\': 45,
    }

    run = True
    heldSegment = None
    selectedSegment = None
    movingMode = False
    while run:
        newMM = pygame.key.get_mods() & pygame.KMOD_ALT
        if newMM and not movingMode:
            try:
                main.makeShape()
            except Exception as e:
                print(f'There was an error generating your shape: {type(e)} - {e}', file=sys.stderr)
        movingMode = newMM

        selectedJoint = (None, None)
        if not movingMode:
            mp = pygame.mouse.get_pos()
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

            SelectedR = pygame.Rect(x, y, w, h)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False
                elif event.key == pygame.K_SPACE:
                    if (not movingMode) and (selectedJoint[0] is None):
                        main.insert_straight(pygame.mouse.get_pos()[0])
                elif event.key == pygame.K_r:
                    main = makeShape.MakeShape(100)
                    heldSegment = None
                    selectedJoint = (None, None)
                    selectedSegment = None
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
                if not movingMode:
                    heldSegment = selectedJoint[0]

                    if selectedSegment is None or not SelectedR.collidepoint(event.pos):
                        selectedSegment = None
                        mp = Point(*event.pos)
                        idx = 0
                        for seg in main.collSegments:
                            p = seg.closestPointTo(mp)
                            if (p[0]-event.pos[0])**2+(p[1]-event.pos[1])**2 <= 5**2:
                                selectedSegment = (seg, idx)
                                break
                            idx += 1
                    else:
                        for i in range(boxes):
                            r = pygame.Rect(x+(boxSze+gap)*i+gap, y+gap, boxSze, boxSze)
                            if r.collidepoint(event.pos):
                                val = list(conns.values())[i]
                                main.setAngs[selectedSegment[1]] = val
                                break

        if pygame.key.get_pressed()[pygame.K_s]:
            if (not movingMode) and (selectedJoint[0] is None):
                main.insert_straight(pygame.mouse.get_pos()[0])

        if heldSegment is not None and (not pygame.mouse.get_pressed()[0]):
            heldSegment = None

        win.fill((10, 10, 10))

        y = win.get_height()/2
        x = (win.get_width()+main.width)/2

        if movingMode:
            selectedSegment = None
            heldSegment = None
            if not pygame.key.get_mods() & pygame.KMOD_SHIFT:
                main.recentre(*pygame.mouse.get_pos())
        else:
            if heldSegment is not None:
                selectedSegment = None
                newx = pygame.mouse.get_pos()[0]
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
            pygame.draw.line(win, (255, 165, 10), selectedSegment[0][0], selectedSegment[0][1], 15)

        segs = main.segments
        for i in range(len(segs)):
            if main.setAngs[i] is not None:
                col = (10, 50, 255)
            else:
                col = (255, 255, 255)
            pygame.draw.line(win, col, segs[i][0], segs[i][1], 10)
        idx = 0
        for j in main.joints:
            if j == selectedJoint[1]:
                pygame.draw.circle(win, (255, 100, 100), j, 5)
            elif idx in (0, len(main.joints)-1):
                pygame.draw.circle(win, (200, 50, 200), j, 5)
            else:
                pygame.draw.circle(win, (100, 100, 255), j, 5)
            idx += 1

        if selectedSegment is not None:
            h = boxSze+gap*2
            w = (boxSze+gap)*boxes+gap
            x, y = (selectedSegment[0][0][0]+selectedSegment[0][1][0]-w)/2, min(selectedSegment[0][0][1], selectedSegment[0][1][1])-h-gap*3
            pygame.draw.rect(win, (125, 125, 125), (x, y, w, h), border_radius=4)
            vals = list(conns.values())
            f = pygame.font.Font(None, boxSze)
            for i in range(boxes):
                r = pygame.Rect(x+(boxSze+gap)*i+gap, y+gap, boxSze, boxSze)
                if vals[i] == main.setAngs[selectedSegment[1]]:
                    if r.collidepoint(pygame.mouse.get_pos()):
                        col = (255, 50, 255)
                    else:
                        col = (10, 50, 255)
                else:
                    if r.collidepoint(pygame.mouse.get_pos()):
                        col = (255, 255, 10)
                    else:
                        col = (255, 255, 255)
                pygame.draw.rect(win, col, r, border_radius=4)
                txt = f.render(list(conns.keys())[i], 1, (0, 0, 0))
                win.blit(txt, (r.x+(r.w-txt.get_width())/2, r.y+(r.h-txt.get_height())/2))

        if movingMode:
            polys = main.generateBounds(100, True, False, True)

            # Outer Polygon
            ps = list(polys[0])
            for p in ps:
                pygame.draw.circle(win, (125, 125, 125), p, 3)
            for i in range(len(ps)-1):
                pygame.draw.line(win, (125, 125, 125), ps[i], ps[i+1], 3)

            # Inner Shapes[Line]
            for i in polys[2]:
                pygame.draw.line(win, (125, 125, 125), i[0], i[1], 3)
                for j in i:
                    pygame.draw.circle(win, (125, 125, 125), j, 2)

        pygame.display.update()

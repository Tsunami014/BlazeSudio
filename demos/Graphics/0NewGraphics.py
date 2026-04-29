"""New Graphics [graphics]"""
def main():
    NAMES = {
        0: "Blank",
        1: "Shapes",
        2: "Transform",
        3: "Images",
        4: "Rotate large",
        5: "Font",
    }
    def PRINT_run(thing, thingcol, nam):
        print(f"\nRunning \033[{thingcol}m{thing}\033[0m with \033[93m{NAMES[nam]}\033[0m:")
    def PRINT_fps(fps):
        print(f"Average FPS: \033[94m{round(fps, 3)}\033[m", end="\r")

    from BlazeSudio.graphicsCore import Core, Ix, AvgClock, Col, Op, Font

    fnt = Font.SysFonts.default()
    fnt.size = 80
    c = AvgClock()
    cur = None
    f = 0
    times = []
    perframe = None
    avgFPS = 0

    def changeOp(new):
        nonlocal cur, f, times, perframe, avgFPS
        if new == cur:
            return
        PRINT_run("new graphics engine", 92, new)
        PRINT_fps(0)
        avgFPS = 0
        cur = new
        f = 1
        times = []

        ops = Op.Fill(Col.White)
        match new:
            case 0: # Blank
                perframe = lambda _: Core(ops)
            case 1: # Shapes
                # It can handle decimals!
                ops += (
                    + Op.Draw.Line((10.5, 10.5), (200.25, 100.75), 15, Col.Black)
                    + Op.Draw.Polygon([(100, 100.5), (200, 300), (0, 300)], 30, Col(80, 100, 250))
                    + Op.Draw.Rect((30.5, 50), (100.25, 80.3333333), 10, Col.Grey, roundness=30)
                    + Op.Draw.Rect(100, 150, 30, 50, 10, Col.Black)
                    + Op.Draw.Circle(300, 300, 10, 5, Col(255, 100, 100))
                    + Op.Draw.Elipse((100, 100), 50, 30, 10, Col(80, 255, 100))
                )
                # Testing entirely fill
                ops += (
                    + Op.Draw.Elipse(700, 100, 30, 70, 0, Col.Black)
                    + Op.Draw.Circle((500, 300.5), 30.5, 0, Col.Black)
                    + Op.Draw.Rect(500, 350, 50, 30, 0, Col.Black)
                    + Op.Draw.Rect((500, 400), (30, 50), 0, Col.Grey, roundness=10)
                )
                # Testing stupid cases. These *should* all appear one after the other in a column
                ops += (
                    + Op.Draw.Rect(500, 500, 0, 0, 5, Col.Black)
                    + Op.Draw.Rect(500, 510, 50, 50, 1, Col.Black, roundness=100)
                    + Op.Draw.Line((500, 570), (500, 570), 5, Col.Black)
                )
                def _1perframe(f):
                    Core(ops + Op.Draw.Circle(f*2, 10, 50, 0, Col(250, 90, 255)))
                perframe = _1perframe
            case 2: # Transform
                rect = Op.Draw.Rect((0, 0), (500, 500), 0, Col.Grey)
                line = Op.Draw.Line((0, 0), (500, 500), 10, Col.Black, **Op.Anchors.Middle)
                lnoff = rect.getNormalisedPos(**Op.Anchors.Middle)
                crop = Op.Crop(0, 0, *rect.rsze)
                def _2perframe(f):
                    Core(ops +
                            (rect +
                                (line @ (Op.Trans.Rotate(f/2) + lnoff + crop))
                             ) @ (100, 100)
                    )
                perframe = _2perframe
            case 3: # Images
                im = Op.Image("text.png")
                im2 = Op.Surf(im.rsze*2, **Op.Anchors.Middle)(im @ Op.Trans.Scale(2, 2))
                def _3perframe(f):
                    Core(ops +
                    (im3 := im2 @ Op.Trans.Rotate(f/2)) @ (
                        -im3.getNormalisedPos() +
                        Op.Crop(0, 0, 400, 400)
                    ) + im2 @ (
                        im2.rsze*(1 + f/720)
                    ))
                perframe = _3perframe
            case 4: # Rotate large
                im = Op.Image("large.jpg", **Op.Anchors.Middle)
                def _4perframe(f):
                    Core(ops + im @ (Op.Trans.Rotate(f/2) + -im.getNormalisedPos()))
                perframe = _4perframe
            case 5: # Font
                def _5perframe(f):
                    Core(ops + fnt("FPS: "+str(avgFPS), (255, 125, 0, 255))@Op.Trans.Translate(80, 80))
                perframe = _5perframe
        ops.freeze()


    Core.resize()
    changeOp(1)

    while Ix.handleBasic():
        if Ix.Keys['1']:
            changeOp(1)
        elif Ix.Keys['2']:
            changeOp(2)
        elif Ix.Keys['3']:
            changeOp(3)
        elif Ix.Keys['4']:
            changeOp(4)
        elif Ix.Keys['5']:
            changeOp(5)
        elif Ix.Keys['0']:
            changeOp(0)
        perframe(f)
        if not Ix.Keys[' ']:
            Core.rend()
        c.tick()
        if f % 20 == 0:
            times.append(c.get_fps())
            times = times[-20:]
            avgFPS = sum(times)/len(times)
            PRINT_fps(avgFPS)
            Core.title = f'FPS: {avgFPS}'
        f = (f + 1) % 720

    Core.Quit()

    #quit() # Uncomment to ignore pygame
    print("\n")

    import pygame
    pygame.init()
    WIN = pygame.display.set_mode()
    c = pygame.time.Clock()
    f = 1
    cur = 1
    init = True
    cache = None
    fnt = pygame.font.Font(None, 80)
    times = []
    r = True
    while r:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                r = False
        ks = pygame.key.get_pressed()
        new = None
        if ks[pygame.K_1]:
            new = 1
        elif ks[pygame.K_2]:
            new = 2
        elif ks[pygame.K_3]:
            new = 3
        elif ks[pygame.K_4]:
            new = 4
        elif ks[pygame.K_5]:
            new = 5
        elif ks[pygame.K_0]:
            new = 0
        if new is not None and new != cur or init:
            cache = None
            if new is not None:
                cur = new
                f = 0
                times = []
            PRINT_run("pygame", 91, cur)
            if init:
                init = False
                PRINT_fps(0)
                avgFPS = 0

        WIN.fill((255, 255, 255))
        match cur:
            case 0: # Blank
                pass
            case 1: # Shapes
                # It cannot handle decimals well, if at all :(
                pygame.draw.line(WIN, 0, (10.5, 10.5), (200.25, 100.75), 15)
                pygame.draw.polygon(WIN, (80, 100, 250), [(100, 100), (200, 300), (0, 300)], 30)
                pygame.draw.rect(WIN, (125, 125, 125), (30, 50, 100, 80), 10, 30)
                pygame.draw.rect(WIN, 0, (100, 150, 30, 50), 10)
                pygame.draw.circle(WIN, (255, 100, 100), (300, 300), 10, 5)
                pygame.draw.ellipse(WIN, (80, 255, 100), (100-50, 100-30, 50*2, 30*2), 10)
                # Testing entirely fill
                pygame.draw.ellipse(WIN, 0, (700-30, 100-70, 30*2, 70*2), 0)
                pygame.draw.circle(WIN, 0, (500, 300), 30.5, 0)
                pygame.draw.rect(WIN, 0, (500, 350, 50, 30), 0)
                pygame.draw.rect(WIN, (125, 125, 125), (500, 400, 30, 50), 0, 10)
                # Testing stupid cases. These all appear one after the other in a column, and should look like;
                pygame.draw.rect(WIN, 0, (500, 500, 0, 0), 5) # Unspecified; in reality, not there..? Would be nice (but too expensive) to make it a dot
                pygame.draw.rect(WIN, 0, (500, 510, 50, 50), 1, 100) # A circle; yay!
                pygame.draw.line(WIN, 0, (500, 570), (500, 570), 5) # Unspecified; in reality, a circle (which is great!)

                pygame.draw.circle(WIN, (250, 90, 255), (f*2, 10), 50, 0)
            case 2: # Transform
                if cache is None:
                    cache = pygame.Surface((500, 500))
                    cache.fill((255, 255, 255))
                    pygame.draw.line(cache, 0, (5, 5), (495, 495), 10)
                pygame.draw.rect(WIN, Col.Grey, (98, 98, 504, 504), 0)
                rotImg = pygame.transform.rotate(cache, f/2)
                diff = ((rotImg.get_width()-cache.get_width())//2, (rotImg.get_height()-cache.get_height())//2)
                WIN.blit(
                    rotImg.subsurface(diff, cache.get_size()), (100, 100)
                )
            case 3: # Images
                if cache is None:
                    cache = pygame.transform.scale2x(pygame.image.load("text.png"))
                nsur = pygame.transform.rotate(cache, f/2)
                WIN.blit(
                    nsur.subsurface((0, 0, min(400, nsur.get_width()), min(400, nsur.get_height()))),
                    (0, 0)
                )
                factor = 1 + f/720
                WIN.blit(
                    cache, (cache.get_width()*factor, cache.get_height()*factor)
                )
            case 4: # Rotate large
                if cache is None:
                    cache = pygame.image.load("large.jpg")
                rot = pygame.transform.rotate(cache, f)
                new_rect = rot.get_rect(center=cache.get_rect().center)
                WIN.blit(rot, new_rect)
            case 5: # Font
                WIN.blit(fnt.render("FPS: "+str(avgFPS), 0, (255, 125, 0)), (80, 80))

        if not ks[pygame.K_SPACE]:
            pygame.display.flip()
        c.tick()
        if f % 20 == 0:
            times.append(c.get_fps())
            times = times[-20:]
            avgFPS = sum(times)/len(times)
            PRINT_fps(avgFPS)
            pygame.display.set_caption(f'FPS: {avgFPS}')
        f = (f + 1) % 720
    print()
    pygame.quit()

from typing import Callable
from BlazeSudio import collisions
from BlazeSudio.Game.world import World
from BlazeSudio.utils.wrap.makeShape import MakeShape
from BlazeSudio.utils.wrap.warp import draw_quad
import concurrent.futures
import numpy as np
import os
import pygame
import math

__all__ = [
    'wrapLevel',
    'wrapSurface',
    'Segment',
    'find_blanks',
    'save',
    'saveData',
    'update'
]

class Segment:
    def __init__(self, startx, endx, angle=None):
        """
        A segment of an image with optional angle constraints!

        Args:
            startx (int): The starting x position of the segment
            endx (int): The ending x position of the segment
            angle (int, optional): The angle to constrain this segment to, or None for nothing. Defaults to None.
        """
        self.pos = [startx, endx]
        self.angle = angle
    
    def __str__(self):
        if self.angle is None:
            return f'<Segment {self.pos[0]}-{self.pos[1]}>'
        return f'<Segment {self.pos[0]}-{self.pos[1]} @{self.angle}°>'
    def __repr__(self): return str(self)

def wrapLevel(
        world: World, 
        lvl: int, 
        collFunc: Callable = None,
        top: int|float = 1,
        bottom: int|float = 0, 
        limit: bool = True, 
        startRot: int|float = 0, 
        constraints: list[Segment] = [],
        halo: list[int] = [0, 0, 0, 0],
        flip: bool = False,
        isIter: bool = False
    ) -> tuple[pygame.Surface]:
    """
    Wrap a level and get it's wrapped surface and also it's collision surface.

    Args:
        world (BlazeSudio.Game.world.World): The world to get the level from.
        lvl (int): The level number.
        collFunc (Callable, optional): The collision function to use. Defaults to None (just removes the tileset).
        top (int|float, optional): The position of the top of the wrapped image. See below 'positioning'. Defaults to 1.
        bottom (int|float, optional): The position of the bottom of the wrapped image. See below 'positioning'. Defaults to 0.
        limit (bool, optional): Whether to limit the warp so it MUST be a height of `pg.get_height()`. Making this False may give some very warped results. Constrains the bottom of the image. Defaults to True.
        startRot (int|float, optional): The starting rotation. Defaults to 0.
        constraints (list[Segment], optional): A list of constraints to apply to the image. Defaults to [].
        halo (list[int, int, int, int], optional): The halo around the image. Defaults to `[0, 0, 0, 0]` (no halo). A good halo is `[255, 255, 255, 10]` (a very faint glow).
        flip (bool, optional): Whether to flip the image. Defaults to False.
        isIter (bool, optional): Whether to return a generator or just run the func itself. Defaults to False (just run the func). The generator is in a format aplicable to `graphics.loading.Progress`.

    Returns:
        tuple[pygame.Surface, pygame.Surface]: The output surface or surfaces which are the wrapped image(s)

    Positioning:
        - When the image is being wrapped, it wraps the width of the image.
        - The top and bottom parameters are the positions of the top and bottom of the image respectively.
        ```
        1 = the width (wrapped) plus a buffer of the image height
        0 = the image width (wrapped)
        -1 = the centroid (or centroid line(s)) of the polygon made by the wrapped image width
        ```
        - Top **must** be >= 0 and bottom **must** be <= 0 and >= -1.
    """
    def wrap():
        pg = world.get_pygame(lvl, transparent_bg=True)
        if collFunc is not None:
            level = world.get_level(lvl).CollisionLayer(collFunc)
            pg2 = level.Render(transparent_bg=True)
        else:
            for i in world.get_level(lvl).layers:
                i.tileset = None  # So it has to render blocks instead >:)
            pg2 = world.get_pygame(lvl, transparent_bg=True)
        if flip:
            pg = pygame.transform.flip(pg, False, True)
            pg2 = pygame.transform.flip(pg2, False, True)
        ret = yield from wrapSurface(pg, top, bottom, limit, startRot, constraints, halo, pg2, True)
        return ret
    
    if isIter:
        return wrap()
    else:
        w = wrap()
        for msg in w:
            pass
        try:
            next(w)
        except StopIteration as e:
            return e.value

def wrapSurface(pg: pygame.Surface, 
                top: int|float = 1,
                bottom: int|float = 0, 
                limit: bool = True,
                startRot: int|float = 0, 
                constraints: list[Segment] = [], 
                halo: list[int] = [0, 0, 0, 0], 
                pg2: bool|pygame.Surface = True,
                isIter: bool = False
    ) -> tuple[pygame.Surface]|pygame.Surface:
    """
    Wrap a pygame surface and optionally it's alpha separately.

    Args:
        pg (pygame.Surface): The pygame surface to wrap.
        top (int|float, optional): The position of the top of the wrapped image. See below 'positioning'. Defaults to 1.
        bottom (int|float, optional): The position of the bottom of the wrapped image. See below 'positioning'. Defaults to 0.
        limit (bool, optional): Whether to limit the warp so it MUST be a height of `pg.get_height()`. Making this False may give some very warped results. Constrains the bottom of the image. Defaults to True.
        startRot (int|float, optional): The starting rotation. Defaults to 0.
        constraints (list[Segment], optional): A list of constraints to apply to the image. Defaults to [].
        halo (list[int, int, int, int], optional): The halo around the image. Defaults to `[0, 0, 0, 0]` (no halo). A good halo is `[255, 255, 255, 10]` (a very faint glow).
        pg2 (bool|pygame.Surface, optional): A pygame surface for the alpha wrapping, or a bool as to whether to return it in the first place. Defaults to True.
            - `pygame.Surface` -> use that for the alpha only wrap
            - `True` -> use `pg` for the alpha wrap
            - `False` -> don't return or calculate an alpha wrap
        isIter (bool, optional): Whether to return a generator or just run the func itself. Defaults to False (just run the func). The generator is in a format aplicable to `graphics.loading.Progress`.

    Returns:
        tuple[pygame.Surface, pygame.Surface]: The output surface or surfaces which are the wrapped image(s)
    
    Positioning:
        - When the image is being wrapped, it wraps the width of the image.
        - The top and bottom parameters are the positions of the top and bottom of the image respectively.
        ```
        1 = the width (wrapped) plus a buffer of the image height
        0 = the image width (wrapped)
        -1 = the centroid (or centroid line(s)) of the polygon made by the wrapped image width
        ```
        - Top **must** be >= 0 and bottom **must** be <= 0 and >= -1.
    """
    def wrap():
        nonlocal pg, pg2
        yield 'Initialising wrap', {'amount': 100, 'done': 0}
        width, height = pg.get_size()
        if isinstance(pg2, pygame.Surface):
            pg2IsPygame = True
            if pg.get_size() != pg2.get_size():
                raise ValueError(
                    'The 2 input surfaces are of different sizes!!!'
                )
        else:
            pg2IsPygame = False
        
        if top < 0 or bottom > 0 or bottom < -1:
            raise ValueError(
                'Top must be >= 0 and bottom must be <= 0 and >= -1'
            )

        # Precompute constraint ranges
        constraint_ranges = [(con.pos[0], con.pos[1]) for con in constraints]
        segs = [x for x in range(width) if not any(start < x < end for start, end in constraint_ranges)]

        npg = pygame.Surface((width, height), pygame.SRCALPHA)
        npg.fill(halo)
        npg.blit(pg, (0, 0))
        pg = npg

        shape = MakeShape(width)
        shape.joints = [(i, 0) for i in segs]
        shape.setAngs = [
            next((con.angle for con in constraints if con.pos[0] == x), None) 
            for x in segs
        ]
        shape.recalculate_dists()
        large, main, small = shape.generateBounds(height, True, False, False)
        largePs = large.toPoints()
        mins = (min(i[0] for i in largePs), min(i[1] for i in largePs))
        shape.joints = [(x - mins[0], y - mins[1]) for x, y in shape.joints]
        large, main, small = shape.generateBounds(height, True, False, True)
        collsegs = shape.collSegments
        largePs = large.toPoints()
        sze = (math.ceil(max(i[0] for i in largePs)), math.ceil(max(i[1] for i in largePs)))
        cir = pygame.Surface(sze, pygame.SRCALPHA)
        if pg2IsPygame:
            cir2 = pygame.Surface(sze, pygame.SRCALPHA)

        angs = [collisions.direction(i.p1, i.p2) for i in collsegs]
        yield 'Initialising lines'

        lns = []
        angs2 = []

        r = (shape.lastRadius + height)*2

        for idx, seg in enumerate(collsegs):
            sin_sum = math.sin(angs[idx]) + math.sin(angs[idx-1])
            cos_sum = math.cos(angs[idx]) + math.cos(angs[idx-1])
            mean_rad = math.atan2(sin_sum, cos_sum)
            avg = math.degrees(mean_rad)
            angs2.append(avg)

            rotated_p1 = collisions.rotate(seg.p1, (seg.p1[0], seg.p1[1]-r), avg)
            rotated_p2 = collisions.rotate(seg.p1, (seg.p1[0], seg.p1[1]+r), avg)
            lns.append(collisions.Line(rotated_p1, rotated_p2))

        lns = collisions.Shapes(*lns)
        hitsLge = collisions.Shapes(*large.toLines())

        def closestTo(li, p):
            return min(li, key=lambda p2: (p2[0]-p[0])**2 + (p2[1]-p[1])**2)

        totd = 0
        total = sum(shape.jointDists)

        points = []
        yield 'Calculating points', {'amount': len(collsegs)+1, 'done': 0}
        def calcPoints(point, idx):
            if top != 0:
                outerp = closestTo(lns[idx].whereCollides(hitsLge), point)
                if top != 1:
                    outerp = ((point[0]-outerp[0]) * top + outerp[0], (point[1]-outerp[1]) * top + outerp[1])
            else:
                outerp = point

            if bottom != 0:
                innerp = small.closestPointTo(collisions.Point(*point))
                if bottom != -1:
                    innerp = ((innerp[0]-point[0]) * abs(bottom) + point[0], (innerp[1]-point[1]) * abs(bottom) + point[1])
            else:
                innerp = point
            
            return [innerp, outerp]
        
        points = [None] * len(collsegs)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(calcPoints, seg.p1, i): i for i, seg in enumerate(collsegs)}
            for future in concurrent.futures.as_completed(futures):
                index = futures[future]
                points[index] = future.result()
                yield 'Calculating points'
        
        points.append(points[0])

        yield 'Calculating subsurfaces', {'amount': len(collsegs), 'done': 0}

        pgSubs = []
        pg2Subs = []
        totd = 0
        pgh, pg2h = pg.get_height(), pg2.get_height() if pg2IsPygame else 0
        for idx, seg in enumerate(collsegs):
            d = shape.jointDists[idx]
            x, w = (totd/total)*width, math.ceil((d/total)*width)
            pgSubs.append(pg.subsurface((x, 0, w, pgh)))
            if pg2IsPygame:
                pg2Subs.append(pg2.subsurface((x, 0, w, pg2h)))
            
            totd += d
            
            yield 'Calculating subsurfaces'
        
        yield 'Calculating segments', {'amount': len(collsegs), 'done': 0}

        def process_segment(idx):
            innerp1, outerp1 = points[idx]
            innerp2, outerp2 = points[idx+1]

            if limit:
                phi1 = collisions.direction(outerp1, innerp1)
                innerp1 = collisions.rotate(outerp1, (outerp1[0], outerp1[1]-height), math.degrees(phi1)+90)
                phi2 = collisions.direction(outerp2, innerp2)
                innerp2 = collisions.rotate(outerp2, (outerp2[0], outerp2[1]-height), math.degrees(phi2)+90)

            poly = [outerp1, outerp2, innerp2, innerp1]

            draw_quad(cir, poly, pgSubs[idx])
            if pg2IsPygame:
                draw_quad(cir2, poly, pg2Subs[idx])

            return d

        with concurrent.futures.ThreadPoolExecutor() as executor:
            for d in executor.map(process_segment, range(len(collsegs))):
                yield 'Calculating segments'

        if pg2 is True: # just mask the output
            surface_array = pygame.surfarray.pixels3d(cir)
            alpha_array = pygame.surfarray.pixels_alpha(cir)

            white = np.array([255, 255, 255])
            black = np.array([0, 0, 0])

            alpha_array[np.all(surface_array == white, axis=-1)] = 0
            alpha_array[np.all(surface_array == black, axis=-1)] = 128  # 50% transparency

            surface = pygame.surfarray.make_surface(surface_array)
            surface = surface.convert_alpha()
            pygame.surfarray.pixels_alpha(surface)[:] = alpha_array
            return cir.copy(), surface.copy()
        elif pg2IsPygame:
            return cir.copy(), cir2.copy()
        return cir.copy()
    if isIter:
        return wrap()
    else:
        w = wrap()
        for msg in w:
            pass
        try:
            next(w)
        except StopIteration as e:
            return e.value

def find_blanks(imgs1: list[pygame.Surface], imgs2: list[pygame.Surface]=None):
    """
    Finds the blank bounding boxes around the input planets. Both will be used to find a box that encompasses both, but the second doesn't *have* to be specified \
    to just use the first instead.

    Args:
        imgs1 (list[pygame.Surface]): The first list of planets.
        imgs2 (list[pygame.Surface], optional): The second list of planets. Defaults to None.

    Returns:
        list[tuple[int, int, int, int]]: The bounding boxes!
    """
    outs = []
    do_img2 = imgs2 is not None
    if not do_img2:
        imgs2 = imgs1
    for img1, img2 in zip(imgs1, imgs2):
        mask = pygame.mask.from_surface(img1, 0)
        bounding_rects = mask.get_bounding_rects()
        if do_img2:
            mask = pygame.mask.from_surface(img2, 0)
            bounding_rects.extend(mask.get_bounding_rects())
        outs.append([
            min(i.x for i in bounding_rects),
            min(i.y for i in bounding_rects),
            max(i.x+i.w for i in bounding_rects),
            max(i.y+i.h for i in bounding_rects),
        ])
        
    return outs

def save(imgs: list[pygame.Surface], 
         fname: str, 
         multiples: int=None, 
         remove_blanks: list[tuple[int]]=None, 
         centreX: bool=False, 
         centreY: bool=False
        ):
    """
    Saves a list of images to a single image file.

    Args:
        imgs (list[pygame.Surface]): The list of images to save.
        fname (str): The filename to save the image to.
        multiples (int, optional): If provided, ensures that the height of each image is a multiple of this value. Defaults to None.
        remove_blank (list[tuple[int]], optional): The blank space to remove in the images, found through `find_blanks`. Defaults to None.
        centreX (bool, optional): Whether to centre the images on the x axis. Defaults to False.
        centreY (bool, optional): Whether to centre the images on the y axis. Defaults to False.
    """
    def modify(x):
        if multiples is None or x%multiples == 0:
            return x
        return x+(multiples-(x%multiples))
    if remove_blanks is not None:
        imgs2 = []
        for idx, img in enumerate(imgs):
            blanks = remove_blanks[idx]
            img2 = pygame.Surface((blanks[2]-blanks[0], modify(blanks[3]-blanks[1])), pygame.SRCALPHA)
            img2.blit(img, (-blanks[0], -blanks[1]))
            imgs2.append(img2)
        imgs = imgs2
    szes = [(i.get_width(), modify(i.get_height())) for i in imgs]
    ms = modify(max(i[0] for i in szes))
    ss = sum(i[1] for i in szes)
    out = pygame.Surface((ms, ss), pygame.SRCALPHA)
    prevh = 0
    for img, sze in zip(imgs, szes):
        act_sze = img.get_size()
        if centreX:
            x = (ms-act_sze[0])/2
        else:
            x = 0
        if centreY:
            y = (sze[1]-act_sze[1])/2
        else:
            y = 0
        out.blit(img, (x, prevh+y))
        prevh += sze[1]

    if not os.path.exists(os.path.dirname(fname)):
        os.makedirs(os.path.dirname(fname))
    pygame.image.save(out, fname)

def saveData(imgs: list[pygame.Surface], fname: str, names: list[str], multiples: int=None, remove_blanks: list[tuple[int]]=None):
    if remove_blanks is not None:
        imgs2 = []
        for idx, img in enumerate(imgs):
            blanks = remove_blanks[idx]
            img2 = pygame.Surface((blanks[2]-blanks[0], blanks[3]-blanks[1]), pygame.SRCALPHA)
            img2.blit(img, (-blanks[0], -blanks[1]))
            imgs2.append(img2)
        imgs = imgs2
    def modify(x):
        if multiples is None or x%multiples == 0:
            return x
        return x+(multiples-(x%multiples))
    szes = [names[idx]+'\x00'+str(modify(i.get_height())) for idx, i in enumerate(imgs)]
    with open(fname, 'w+') as f:
        f.write('\n'.join(szes))

def update(img: pygame.Surface, 
           replaceName: str, 
           fname: str, 
           dataFname: str, 
           multiples: int=None, 
           remove_blanks: tuple[int]=None, 
           centreX: bool=False, 
           centreY: bool=False
        ):
    toth = 0
    thish = 0
    thisidx = 0
    with open(dataFname) as f:
        fc = f.read()
        for ln in fc.split('\n'):
            name, h = ln.split('\x00')
            if name == replaceName:
                thish = int(h)
                thisidx += 1 + len(name)
                break
            toth += int(h)
            thisidx += 2 + len(name) + len(h)
    
    out = pygame.image.load(fname)

    if remove_blanks is not None:
        blanks = remove_blanks
        img2 = pygame.Surface((blanks[2]-blanks[0], blanks[3]-blanks[1]), pygame.SRCALPHA)
        img2.blit(img, (-blanks[0], -blanks[1]))
        img = img2
    def modify(x):
        if multiples is None or x%multiples == 0:
            return x
        return x+(multiples-(x%multiples))
    
    ms = modify(img.get_width())
    out2 = out.subsurface((0, toth+thish, out.get_width(), out.get_height()-toth-thish))
    if ms > out.get_width():
        if centreX:
            x = (ms-out.get_width())/2
        else:
            x = 0
        out1 = pygame.Surface((ms, toth), pygame.SRCALPHA)
        out1.blit(out, (x, 0))
        nout2 = pygame.Surface((ms, (out.get_height()-toth-thish)), pygame.SRCALPHA)
        nout2.blit(out2, (x, 0))
        out2 = nout2
    else:
        ms = out.get_width()
        out1 = out.subsurface((0, 0, out.get_width(), toth)).copy()
        out2 = out2.copy()
    
    thisOut = pygame.Surface((ms, img.get_height()), pygame.SRCALPHA)
    if centreX:
        x = (ms-img.get_width())/2
    else:
        x = 0
    if centreY:
        y = (thisOut.get_height()-img.get_height())/2
    else:
        y = 0
    thisOut.blit(img, (x, y))

    h1, h2, h3 = out1.get_height(), thisOut.get_height(), out2.get_height()
    out = pygame.Surface((ms, modify(h1+h2+h3)), pygame.SRCALPHA)
    out.blit(out1, (0, 0))
    out.blit(thisOut, (0, h1))
    out.blit(out2, (0, modify(h1+h2)))

    pygame.image.save(out, fname)

    writeHei = str(modify(thisOut.get_height()))
    if replaceName in fc:
        new = fc[:thisidx] + writeHei + '\n' + fc[thisidx+len(writeHei):]
    else:
        new = fc + f'\n{replaceName}\x00{writeHei}'

    with open(dataFname, 'w') as f:
        f.write(new.replace('\n\n', '\n').strip('\n'))

if __name__ == '__main__':
    pygame.init()
    pygame.display.set_mode((1, 1))
    sur = pygame.Surface((1,2), pygame.SRCALPHA)
    sur.set_at((0, 0), (255, 255, 255))
    sur.set_at((0, 1), (0, 0, 0))
    wrapSurface(pygame.transform.scale(sur, (500, 300)), 0.5, -0.5)

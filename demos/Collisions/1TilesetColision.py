"""Tileset collision [graphics & collisions]"""
def main():
    from BlazeSudio.graphics import Screen, Loading, options as GO, GUI
    from BlazeSudio.utils import genCollisions as gen
    from functools import partial
    import pygame

    tset = pygame.image.load('sampleTileset.png')

    class Main(Screen):
        def getTile(self, idx):
            if idx is None:
                return
            self.poly = None
            self.tile = tset.subsurface((idx*32, 0, 32, 32))

        @Loading.decor
        def calcPoly(slf, self):
            chosen = self.opts.index(self.chooser.get())
            if chosen == 0:
                self.poly = None
            elif chosen == 1:
                self.poly = [(0, 0), (32, 0), (32, 32), (0, 32)]
            elif chosen == 2:
                self.poly = gen.bounding_box(self.tile)
            elif chosen == 3:
                self.poly = gen.corners(self.tile)
            elif chosen == 4:
                self.poly = gen.approximate_polygon(self.tile)

        def __init__(self):
            self.getTile(0)
            self.opts = [
                'No collisions',
                'Cover entire shape',
                'Bounding box',
                'Corners',
                'Trace shape'
            ]
            super().__init__()

        def _Event(self, event):
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.calcPoly(self)

        def _LoadUI(self):
            self.layers[0].add('Main')

            PCTOP = GO.PNEW((0.5, 0), (1, 0), (True, False))
            self.scale = GUI.NumInputBox(PCTOP, 100, GO.RNONE, start=None, empty=10, minim=1, maxim=30, placeholder='Scale by size', decimals=2)
            chooser = GUI.DropdownButton(PCTOP, ['Tile %i'%i for i in range(tset.get_width()//32)], func=lambda i: self.getTile(i))
            self.chooser = GUI.DropdownButton(PCTOP, self.opts)

            goBtn = GUI.Button(GO.PCBOTTOM, GO.CGREEN, 'Go!', func=partial(self.calcPoly, self))

            self['Main'].extend([
                self.scale,
                chooser,
                self.chooser,
                goBtn
            ])

        def _Tick(self):
            scale = self.scale.get()

            def outPos(x, y):
                center_x = (self.size[0] - 32 * scale) / 2
                center_y = (self.size[1] - 32 * scale) / 2
                return (x * scale + center_x, y * scale + center_y)

            self.WIN.blit(pygame.transform.scale(self.tile, (32*scale, 32*scale)), outPos(0, 0))

            if self.poly is not None:
                pygame.draw.polygon(self.WIN, (125, 125, 125), [outPos(*p) for p in self.poly], 4)

    Main()()

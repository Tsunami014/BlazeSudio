"""Lorem Ipsum [oldgraphics]"""
def main():
    from BlazeSudio.graphics import Screen, RunInstantly, Loading, options as GO, GUI

    class Test(Screen, RunInstantly):
        def _LoadUI(self):
            self.layers[0].add('speshs')
            @Loading.decor
            def load(slf):
                S2 = GUI.ScrollableFrame(GO.PCCENTER, (900, 700), (2000, 11000))
                S2.layers[0].add('alls')
                with open('lorem.txt') as f:
                    lorem = f.read()
                S2['alls'].append(GUI.Text(GO.PCTOP, lorem, allowed_width=1900))
                self['speshs'].append(S2)
            fin, _ = load()
            if not fin:
                self.Abort()

    Test()

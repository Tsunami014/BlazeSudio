"""New GUI [graphics]"""
def main():
    from BlazeSudio.graphicsCore import Draw
    from BlazeSudio.GUI import OpElm
    from BlazeSudio.GUI import UI, Layouts, Elms

    UI(
        Layouts.Vert()
            .add_stretch(1)
            .add_elm(Layouts.Horiz()
                .add_stretch(1)
                .add_elms([
                    OpElm(Draw.Rect((0,0), (100,100),0,(125,125,125,255))),
                    Elms.Text("This is a test!"), # TODO: Size
                    OpElm(Draw.Rect((0,0), (100,100),0,(125,125,125,255))),
                    ])
                .add_stretch(1)
            )
            .add_stretch(1)
    )

    UI.resize(800, 500)
    UI.Run()

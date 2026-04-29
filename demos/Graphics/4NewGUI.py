"""New GUI [graphics]"""
def main():
    from BlazeSudio.graphicsCore import Draw
    from BlazeSudio.GUI import OpElm
    from BlazeSudio.GUI import UI, Layouts, Elms

    UI(
        Layouts.CentreBoth(
            OpElm(Draw.Rect((0,0), (100,100),0,(125,125,125,255))),
            Layouts.CentreVert(
                Elms.Text("This is a test!"),
            ),
            OpElm(Draw.Rect((0,0), (100,100),0,(125,125,125,255))),
        )
    )

    UI.resize(800, 500)
    UI.Run()

"""New GUI [graphics]"""
def main():
    from BlazeSudio.graphicsCore import Draw
    from BlazeSudio.GUI import OpElm
    from BlazeSudio.GUI import UI, Layouts, Elms

    UI(
        Layouts.CentreVert(
            Layouts.CentreHoriz(
                OpElm(Draw.Rect((0,0), (100,100),0,(125,125,125,255))),
                Layouts.CentreVert(
                    Elms.Text("This is a test!"),
                ),
                OpElm(Draw.Rect((0,0), (100,100),0,(125,125,125,255))),
            ),
            Elms.Text("I hope you really like this extremely super duper very long text as it is quite long and it should wrap around the screen.\nNewline! Yay!")
        )
    )

    UI.resize(800, 500)
    UI.Run()

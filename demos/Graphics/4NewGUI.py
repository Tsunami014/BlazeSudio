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
                    Elms.Text("This is a test!", opts=None),
                ),
                OpElm(Draw.Rect((0,0), (100,100),0,(125,125,125,255))),
            ),
            Layouts.CentreHoriz( # The text only centres to its own max width (the longest line), so we need to centre it again
                Elms.Text(
                    "I hope you really like this extremely super long very long text as it is quite long and it should wrap around the screen right around here and if it does not then maybe try resizing the screen I guess because otherwise you won't be able to see the epic wrapping capabilities of this!\nNewline! Yay!",
                    opts=(o:=Elms.Text.O).CentreAlign | o.Defaults)
            )
        )
    )

    UI.resizable = True
    UI.Run()

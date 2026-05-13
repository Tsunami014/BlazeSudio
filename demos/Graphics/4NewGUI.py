"""New GUI [graphics]"""
def main():
    from BlazeSudio.graphicsCore import Draw
    from BlazeSudio.GUI import OpElm
    from BlazeSudio.GUI import UI, Layouts, Elms, Input

    txt = Elms.Text("")
    clks = 0
    def onclk(_=None):
        nonlocal clks
        txt.txt = f"{clks} clicks!"
        clks += 1
    onclk()
    UI(
        Layouts.CentreVert(
            Layouts.CentreHoriz(
                OpElm(Draw.Rect((0,0), (100,100),0,(125,125,125,255))),
                Layouts.CentreVert(
                    Input.Button(
                        Elms.Text("This is a test!", opts=None),
                        onclick=onclk
                    ),
                ),
                Layouts.CentreVert(txt),
                OpElm(Draw.Rect((0,0), (100,100),0,(125,125,125,255))),
            ),
            Layouts.AlignCentre(
                Elms.Text("I hope you really like this extremely super long very long text as it is quite long and it is very nice and long and epic.\nNewline! Yay!")
            )
        )
    )

    UI.resizable = True
    UI.Run()

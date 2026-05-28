"""New GUI [graphics]"""
def main():
    from BlazeSudio.graphicsCore import Draw
    from BlazeSudio.GUI import OpElm
    from BlazeSudio.GUI import UI, Lays, Elms, Input

    txt = Elms.Text("")
    clks = 0
    def onclk(_=None):
        nonlocal clks
        txt.txt = f"{clks} clicks!"
        clks += 1
    onclk()
    UI(
        Lays.VBox[None,
            Lays.HBox[None,
                OpElm(Draw.Rect((0,0), (100,100),0,(125,125,125,255))),
                Input.Button(
                    Elms.Text("This is a test!", opts=None),
                    onclick=onclk
                ),
                txt,
                OpElm(Draw.Rect((0,0), (100,100),0,(125,125,125,255))),
            None],
            Elms.Text("I hope you really like this extremely super long very long text as it is quite long and it is very nice and long and epic.\nNewline! Yay!"
                ).AlignC,
            Input.InputBox(placeholder="Type here!",
                opts=(O:=Input.InputBox.O).Default|O.Multiline).AlignC,
        None]
    )

    UI.resizable = True
    UI.Run()

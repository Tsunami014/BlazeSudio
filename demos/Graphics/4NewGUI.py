"""New GUI [graphics]"""
def main():
    from BlazeSudio.graphicsCore import Draw
    from BlazeSudio.GUI import OpElm
    from BlazeSudio.GUI import UI, Lays, Elms, Input, Col, Term

    txt = Elms.Text("")
    clks = 0
    def onclk(_=None):
        nonlocal clks
        txt.txt = f"{clks} clicks!"
        clks += 1
    onclk()
    mtxt = Elms.Text("", opts=None).AlignC()
    def settxt(t):
        mtxt.txt = t

    t = Term()
    @t.onmessage
    def _(t):
        print(t)
    t.oncmd("set")(settxt)

    UI(
        Lays.Stack[
            Lays.VBox[None,
                mtxt,
                Input.InputBox(placeholder="Type then press enter!", bordercol=Col.Indigo, onenter=settxt).AlignC(),
                Lays.HBox[None,
                    OpElm(Draw.Rect((0,0), (100,100),0,(125,125,125,255))),
                    Input.Button(
                        Elms.Text("This is a test!"),
                        onclick=onclk
                    ),
                    txt,
                    OpElm(Draw.Rect((0,0), (100,100),0,(125,125,125,255))),
                None],
                Elms.Text("I hope you really like this extremely super long very long text as it is quite long and it is very nice and long and epic. I totally spent so long on it.\nNewline! Yay!"
                    ).AlignC(),
                Input.InputBox(placeholder="Type multiline here!",
                    opts=(O:=Input.InputBox.O).Default|O.Multiline).AlignC(),
            None],
            Lays.Offset(10, 10, Elms.Text("Alt+/ to open terminal").PositionT().AlignL()),
            Lays.VBox[None, Lays.HBox[None, Lays.Offset(-10, -10,
                Input.Button(Elms.Text("The do-nothing\nbutton").AlignR(), Col.Secondary).PositionB()
            )]],
        t]
    )

    UI.resizable = True
    UI.Run()

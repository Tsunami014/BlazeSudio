"""Image wrapping [image]"""
def main():
    from BlazeSudio.GUI import UI, Lays, Elms
    UI.resize()

    UI(
        Lays.HBox[None,
            Lays.VBox[10,
                Elms.Text("Input").AlignC(),
            10,
            10, Elms.HLine((0,0,0,255), 5),
            None,
                Elms.Text("Input image here").AlignC(),
            None],
        None,10,Elms.VLine((0,0,0,255), 10),10,None,
            Lays.VBox[10,
                Elms.Text("Output").AlignC(),
            None,
                Elms.Text("Output image here").AlignC(),
            None],
        None]
    ).Run()

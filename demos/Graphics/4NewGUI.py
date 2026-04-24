"""New GUI [graphics]"""
def main():
    from BlazeSudio.graphicsCore import Draw
    from BlazeSudio.GUI import UI, HLayout, Input

    UI(
        HLayout(
            Draw.Rect((0,0), (100,100),0,(0,0,0,255)),
            Draw.Rect((0,0), (100,100),0,(125,125,125,255))
        )
    )

    UI.resize(800, 500)
    UI.Run()

"""New GUI [graphics]"""
def main():
    from BlazeSudio.graphicsCore import Draw, Trans
    from BlazeSudio.graphicsCore.base import Anchors
    from BlazeSudio.GUI import UI, HLayout, OpElm, Input

    UI(
        HLayout()
            .add_stretch(1)
            .add_elms([
                OpElm(Draw.Rect((0,0), (100,100),0,(0,0,0,255), **Anchors.Middle)) @ Trans.Rotate(45),
                OpElm(Draw.Rect((0,0), (100,100),0,(125,125,125,255)))
                ])
            .add_stretch(1)
    )

    UI.resize(800, 500)
    UI.Run()

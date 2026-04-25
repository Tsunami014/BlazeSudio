"""Graphics [graphics]"""
def main():
    import BlazeSudio.graphics.options as GO
    from BlazeSudio.graphics import Screen, Loading, Progressbar, GUI
    from BlazeSudio.graphics.base import HiddenStatus
    from BlazeSudio.graphics.base import ReturnState
    import pygame
    from time import sleep
    pygame.init()
    @Loading.decor
    def test_loading(slf):
        slf['i'] = 0
        for slf['i'] in range(10):
            sleep(1)
    
    @Progressbar.decor(10)
    def test_loading2(slf):
        yield '0'
        slf['i'] = 0
        for slf['i'] in range(10):
            sleep(1)
            yield slf['i']+1
    
    class Test(Screen):
        def __init__(self, txt):
            super().__init__(GO.CWHITE)
            self.txt = txt
        
        def _LoadUI(self): # Load the graphics in!
            CTOP = GO.PNEW((0.5, 0), (1, 0), (True, False)) # Bcos usually the Center Top makes the elements stack down, so I make a new thing that stacks sideways
            LBOT = GO.PNEW((0, 1), (0, -1)) # Going up instead of right
            RTOP = GO.PNEW((1, 0), (-1, 0)) # Going left instead of down
            self.layers[0].add_many([
                # You can name these whatever you want, but I like to keep them the same as the type.
                'TB',
                'texts',
                'space',
                'buttons',
                'events',
                'speshs',
                'endElms', # These will be the ones I find in the GO.ELAST event
            ])
            # I chose this because you can see the different sections of the screen, but you can do what you want; as long as they end up on the list it's ok.
            # I also showcase below many ways of doing the same things.
            tb = GUI.DebugTerminal(jump_to_shortcut=pygame.K_F5)
            for word in ['hi', 'bye', 'hello', 'goodbye', 'greetings', 'farewell']:
                f = lambda *args, word=word: self['events'].append(GUI.Toast(  # noqa: E731
                    f'{word[0].upper()}{word[1:]}{" " if len(args) > 0 else ""}{", ".join(args[:-1])}{" & " if len(args) > 1 else ""}{args[-1]}!'
                ))
                f.__doc__ = f"{word} *<str> : Says {word} with the given arguments"
                tb.addCmd(word, f)
            self['TB'].append(tb)

            f = GUI.ScaledByFrame(GO.PRBOTTOM, (500, 400))
            self['speshs'].append(f)
            f.layers[0].add('Alls')
            f['Alls'].extend([
                GUI.Text(GO.PLTOP, 'Scaled Frame', GO.CBLUE),
                GUI.Empty(GO.PLTOP, (0, 15)),
                GUI.Text(GO.PLTOP, 'Change scale:', GO.CGREEN),
                (cs := GUI.NumInputBox(GO.PLTOP, 100, GO.RHEIGHT, empty=2, minim=1, placeholdOnNum=None, decimals=True))
            ])
            self.changeScale = cs

            self['texts'].extend([
                GUI.Text(GO.PCCENTER, 'This is a cool thing', GO.CBLUE),
                (ivt := GUI.Text(GO.PCCENTER, '*Sorry*, I meant a cool *TEST*', GO.CRED)),
                (txt := GUI.Text(GO.PCCENTER, self.txt, GO.CGREEN))
            ])
            self.Invisi_T = ivt
            self.txt = txt

            self.inp = GUI.InputBox(GO.PCCENTER, 500, GO.RHEIGHT)
            self['endElms'].append(self.inp)
            self['space'].append(GUI.Empty(GO.PCCENTER, (0, 50)))
            self['endElms'].append(GUI.NumInputBox(GO.PCCENTER, 100, minim=-255, maxim=255, placeholdOnNum=None))
            self['endElms'].append(GUI.NumInputBox(GO.PCCENTER, 100, minim=-255, maxim=255, placeholder='Type decimal here!', empty=100, decimals=3))
            self['space'].append(GUI.Empty(GO.PCCENTER, (0, 50)))
            self['endElms'].append(GUI.DropdownButton(GO.PCCENTER, ['HI', 'BYE']))

            self['space'].append(GUI.Empty(LBOT, (0, 20)))
            self['buttons'].append(GUI.Button(LBOT, GO.CYELLOW, 'Button 1 :D'))
            self['texts'].append(GUI.Text(LBOT, 'Buttons above [^] and below [v]', GO.CBLUE))
            self.PopupBtn = GUI.Button(LBOT, GO.CMAUVE, 'Popup test')
            self.TextboxBtn = GUI.Button(LBOT, GO.CBLUE, 'Textbox test')
            self.LoadingBtn = GUI.Button(LBOT, GO.CGREEN, 'Loading test')
            self.LoadingBtn2 = GUI.Button(LBOT, GO.CGREY, 'Progressbar loading test')
            self.exitbtn = GUI.Button(GO.PLCENTER, GO.CRED, 'EXIT', GO.CWHITE, func=lambda: self.Abort())
            self['buttons'].extend([
                self.PopupBtn,
                self.TextboxBtn,
                self.LoadingBtn,
                self.LoadingBtn2,
                self.exitbtn
            ])

            self['texts'].extend([
                GUI.Text(CTOP, 'Are you '),
                GUI.Text(CTOP, 'happy? ', GO.CGREEN),
                GUI.Text(CTOP, 'Or sad?', GO.CRED)
            ])

            self.switches = [
                GUI.Switch(RTOP, 40, 2),
                GUI.Switch(RTOP, default=True),
            ]
            self['endElms'].extend(self.switches)
            self.colour = GUI.ColourPickerBTN(RTOP)
            self['endElms'].extend([
                self.colour,
                GUI.Empty(RTOP, (10, 10)),
                (mdInp := GUI.InputBox(RTOP, 600, GO.RHEIGHT, placeholder='Type in Markdown!'))
            ])
            mdInp.useMD = True

            L = GUI.GridLayout(GO.PCBOTTOM, outline=5)
            self['speshs'].append(L)
            L.grid = [
                [GUI.Text(L.LP, '**HI**'), None, GUI.Text(L.LP, '*BYE*')],
                [GUI.Text(L.LP, '***YES***'), GUI.Checkbox(L.LP), GUI.Text(L.LP, 'NO')],
                [GUI.Checkbox(L.LP, 20, check_size=10), GUI.Checkbox(L.LP, thickness=2), GUI.Checkbox(L.LP, check_size=40)],
                [GUI.Button(L.LP, GO.CORANGE, '*Hel-**looo!!***'), None, (sw := GUI.Switch(L.LP))]
            ]
            self.sw = sw

            TOPLEFT = GO.PSTATIC(10, 10) # Set a custom coordinate that never changes
            S = GUI.ScrollableFrame(TOPLEFT, (250, 200), (400, 450))
            self['speshs'].append(S)
            # This is another way of setting out your Stuff; having everything under one name.
            S.layers[0].add('Alls')
            S['Alls'].extend([
                GUI.Empty(GO.PCTOP, (0, 10)),
                GUI.Text(GO.PCTOP, 'Scroll me!', GO.CBLUE),
                GUI.Empty(GO.PCTOP, (0, 50)),
                GUI.InputBox(GO.PCTOP, 200, GO.RHEIGHT, weight=GO.SWLEFT),
                GUI.Empty(GO.PCTOP, (0, 50)),
                GUI.Button(GO.PCTOP, GO.CGREEN, 'Press me!', func=lambda: self.txt.set('### You pressed the button in the Scrollable :)')),
                GUI.Empty(GO.PCTOP, (0, 50)),
                GUI.Text(GO.PCTOP, 'Auto adjust scrollable height', GO.CORANGE, allowed_width=200),
                GUI.Switch(GO.PCTOP, speed=0.5)
            ])
        def _Tick(self): # This runs every 1/60 secs (each tick)
            # Return False if you want to quit the screen. This is not needed if you never want to do this.
            self['speshs'][0].scale = self.changeScale.get()
            S = self['speshs'][2]
            e = S['Alls'][-1]
            if e.get():
                S.sizeOfScreen = (S.sizeOfScreen[0], e.stackP()[1]+e.size[1]+30)
            else:
                S.sizeOfScreen = (S.sizeOfScreen[0], 450)
        def _ElementClick(self, obj): # Some UI element got clicked!
            if obj.type == GO.TBUTTON:
                # This gets passed 'obj': the element that got clicked.
                if obj == self.LoadingBtn:
                    succeeded, ret = test_loading()
                    self.txt.set('Ran for %i seconds%s' % (ret['i']+1, (' **Successfully!** :)' if succeeded else ' And *failed* :(')))
                elif obj == self.LoadingBtn2:
                    succeeded, ret = test_loading2()
                    self.txt.set('Ran for %i seconds%s' % (ret['i']+1, (' **Successfully!** :)' if succeeded else ' And *failed* :(')))
                elif obj == self.TextboxBtn:
                    bot = GO.PNEW((0.5, 1), (0, 0), (True, False))
                    dialog_box = GUI.TextBoxAdv(bot, text='HALOOO!!')
                    dialog_box.set_indicator()
                    dialog_box.set_portrait()
                    self['events'].append(dialog_box)
                    self.idx = 0
                elif obj == self.PopupBtn:
                    pop = GUI.PopupFrame(GO.PCCENTER, (350, 300))
                    pop.layers[0].add('Alls')
                    def rmpop(pop):
                        pop.remove()
                        return ReturnState.DONTCALL
                    pop['Alls'].extend([
                        GUI.Empty(GO.PCTOP, (0, 10)),
                        GUI.Text(GO.PCTOP, '# Popup'),
                        GUI.Text(GO.PCCENTER, 'This is an **example** of a popup!', allowed_width=250),
                        GUI.Button(GO.PRTOP, GO.CYELLOW, '❌', func=lambda p=pop: rmpop(p)),
                        GUI.Empty(GO.PCBOTTOM, (0, 10)),
                        GUI.InputBox(GO.PCBOTTOM, 250, GO.RNONE, 'Example textbox', maxim=16),
                    ])
                    self['events'].append(pop) # I know it's not an event, but o well.
                else:
                    self.txt.set(obj.txt) # put name of button in middle
            elif obj.type == GO.TTEXTBOX:
                if self.idx == 0:
                    obj.set("Happy coding!")
                    self.idx = 1
                else: 
                    obj.remove()
            elif obj.type == GO.TINPUTBOX:
                self.txt.set(obj.get().strip())
            elif obj.type == GO.TSWITCH:
                if obj == self.sw:
                    if obj.get():
                        self.Invisi_T.hiddenStatus = HiddenStatus.GONE
                    else:
                        self.Invisi_T.hiddenStatus = HiddenStatus.SHOWING
        def _Event(self, event): # When something like a mouse or keyboard button is pressed. Is passed 'element' too, but this time it is an event
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s and event.mod & pygame.KMOD_CTRL:
                    self['events'].append(GUI.Toast('Saved! (Don\'t worry - this does nothing)', GO.CGREEN))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_RIGHT:
                opts = ['HI', 'BYE', 'HI AGAIN']
                def dropdownSelect(resp):
                    if isinstance(resp, int):
                        self.txt.set(opts[resp])
                self['events'].append(GUI.Dropdown(self, pygame.mouse.get_pos(), opts, func=dropdownSelect))
        def _Last(self, aborted):
            # This also gets passed 'aborted': Whether you aborted or exited the screen
            S = self['speshs'][2]
            return { # Whatever you return here will be returned by the function
                'Aborted?': aborted, 
                'endElms': self['endElms']+[
                    # These are the input and the switch
                    S['Alls'][3],
                    S['Alls'][-1],
                ]}
    
    print(Test('Right click or press anything or press ctrl+s!')())
    pygame.quit() # this here for very fast quitting

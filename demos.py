import sys
import os

def get_demos():
    import importlib.util
    cmds = {}
    pth = os.path.abspath(os.path.join(__file__, "..", "demos"))
    for it in os.listdir(pth):
        full = os.path.join(pth, it)
        if '.' not in it and it[0] != '_' and os.path.isdir(full):
            alls = []
            for it2 in os.listdir(full):
                if it2[0] not in "_." and it2[-3:] == ".py":
                    try:
                        spec = importlib.util.spec_from_file_location(
                            "demo_"+it2[:-3], os.path.join(full, it2)
                        )
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        if not hasattr(mod, 'main'):
                            print(f"File demos/{it}/{it2} has no main function!")
                            continue
                        nam = getattr(mod, "__doc__", it2[1:-3].capitalize())
                        alls.append((it2[0], nam, os.path.join(full, it2), mod))
                    except ImportError as e:
                        print(f"Error importing file demos/{it}/{it2}! {type(e)}: {e}")
            alls.sort(key=lambda x: x[0])
            cmds[it] = alls
    return cmds

def cmdList(cmds):
    out = []
    for _, commands in cmds.items():
        out.extend(commands)
    return out

def run(args):
    _, nam, pth, mod = args
    print('loading demo %s...'%nam)
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    os.chdir(os.path.dirname(pth))
    mod.main()

if __name__ == '__main__':
    cmds = get_demos()

    def runFn(idx):
        li = cmdList(cmds)
        if idx < 0 or idx > len(li):
            raise ValueError(
                'Invalid input number!'
            )
        run(li[idx])

    import sys
    if len(sys.argv) == 1:
        pass
    elif len(sys.argv) == 2:
        idx = int(sys.argv[1])
        runFn(idx)
        exit()
    else:
        raise ValueError(
            'Too many arguments!'
        )

    try:
        import tkinter as Tk
        has_tk = True
        root = Tk.Tk()
    except ImportError:
        print("You don't have tkinter installed. Using the command line instead.\n")
        has_tk = False

    idx = 0
    for nam, commands in cmds.items():
        if has_tk:
            Tk.Label(root, text=nam).pack()
        else:
            print('\n'+nam)
        for args in commands:
            if has_tk:
                Tk.Button(root, text=args[1],
                    command=(lambda ars=args: root.destroy() or run(ars))
                ).pack()
            else:
                print(f'{idx}: {args[1]}')
            idx += 1
    
    if has_tk:
        root.after(1, lambda: root.attributes('-topmost', True))
        def tk_abort(exc, val, tb):
            raise val.with_traceback(tb)
        root.report_callback_exception = tk_abort
        root.mainloop()
    else:
        idx = None
        try:
            idx = int(input('Enter the number of the demo you want to run > '))
        except ValueError:
            print('You entered an invalid number. Exiting.')
            idx = None
        except IndexError:
            print('You entered a number that is not in the list. Exiting.')
            idx = None
        except KeyboardInterrupt:
            print('Exiting.')
            idx = None
        if idx is not None:
            runFn(idx)


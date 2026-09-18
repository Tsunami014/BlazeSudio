This is still in development, but look forward to v4.0.0!

## Quicklinks
| [Requirements](#requirements) | [Demos](#demos) | [Installation](#installation) |
|:-:|:-:|:-:|

## Contents
Blaze Sudio is a game engine for Python containing;

### A graphics engine
- Which is faster than Pygame! (Compiled with cython) It's even faster when not displaying anything, which is cool.
- Uses an "operation stack", so instead of running each transformation on the surface one by one it applies all operations on the surface when displaying
- And is more Pythonic than Pygame too, including type hints, docstrings and many magic methods
- And comes with many GUI elements for ease of use!

### A collision engine
- Can collide various shapes (e.g. points, lines, circles, rectangles, etc.) efficiently (compiled with cython)
- Has built-in functions for handling how shapes collide with other shapes when moving, so you don't have to worry!
- Uses complex maths to calculate where objects hit each other when moving and calculates rebound position and velocity, so *clipping through shapes is impossible*

### Many old things I need to improve/remove/add to
Yes, this project is extremely still in development. But v4.0.0 should be fully working! Look forward to it!

## Requirements
- Python 3.11+
- Linux or Windows (although I don't test on Windows, but I'll still fix anything *reasonable* if you find a problem)

## Demos
To run the demos;

1. Clone the repo (with `--depth 5` so you're not pulling all of history)
2. Install requirements
3. Run `demos.py`

```bash
git clone --depth 5 https://github.com/Tsunami014/Blaze-Sudio.git
cd Blaze-Sudio
pip install .[all]
python3 demos.py
```

## Installation
Just run `pip install BlazeSudio[things]` with whatever requirements you need from below

### Optional requirements
Some parts of the library require external libraries, which are installed via the `[brackets]` when pip installing;

- The collisions module requires `[collisions]`
- The graphics module requires `[graphics]`
- The game module requires `[game]`. **This also installs the graphics and collisions**
- The `[all]` installs everything.

You can also install multiple of these at a time like so: `pip install Blaze-Sudio[graphics,collisions]`.

### Installing from sauce 🍅
- Git clone and pip install (`--depth 5` clones only the most recent 5 commits, because the history of this project is huge)
```bash
git clone --depth 5 https://github.com/Tsunami014/Blaze-Sudio.git
cd Blaze-Sudio
pip install .[all]
```

- OR use the one liner
```bash
pip install "Blaze-Sudio[all] @ git+https://github.com/Tsunami014/Blaze-Sudio.git"
```


## Fun facts
- This project was started before AI existed (back in ye olde 2023/2024, origins are debatable), and many of the original contents including the whole physics engine was coded entirely by me without the help from AI.
- Because this project is so old, I changed coding styles a LOT during development.
- The physics engine does not use any external library, but Shapely is there in case there are things you want to do that I have not provided
- This project will be renamed at some point before v4.0.0 releases to Apricot
- Here is the star history chart:
[![Star History Chart](https://api.star-history.com/svg?repos=Tsunami014/Blaze-Sudio&type=Timeline)](https://star-history.com/#Tsunami014/Blaze-Sudio&Timeline)

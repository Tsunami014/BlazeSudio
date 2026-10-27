This is still in development, but look forward to v4.0.0!

## Quicklinks
| [Requirements](#system-requirements) | [Demos](#demos) | [Installation](#installation) |
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

### Various utils
Including:

#### An image wrapper
- There is a base shape creator, which takes a bunch of points and wraps it into a closed polygon.
- And then you can use this with images to wrap images into shapes!
- This is made with just numpy and is compiled with cython for speed

### Many old things I need to improve/remove/add to
Yes, this project is extremely still in development. But v4.0.0 should be fully working! Look forward to it!

## System requirements
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
pip install .
python3 demos.py
```

## Installation
Just run `pip install BlazeSudio`

### Installing from sauce 🍅
- Git clone and pip install (`--depth 5` clones only the most recent 5 commits, because the history of this project is huge)
```bash
git clone --depth 5 https://github.com/Tsunami014/Blaze-Sudio.git
cd Blaze-Sudio
pip install .
```

- OR use the one liner
```bash
pip install "Blaze-Sudio @ git+https://github.com/Tsunami014/Blaze-Sudio.git"
```


## Fun facts
- This project was started before AI existed (back in ye olde 2023/2024, origins are debatable), and many features, including the whole physics engine and image wrapping, were created entirely by me without help from AI in any way (because it wasn't good enough to help at all).
- The only module I even partially vibe coding was the graphics engine internals (for drawing shapes and stuff to numpy arrays). The rest is all mostly me.
- I turn/will turn (not bothered to change this until I find it again lol) 18 in 2027. So I also made the physics engine etc. before I was/am an adult. Which is my greatest flex hehe
- Because this project is so old (in terms of my life), I changed coding styles a LOT during development, and because it's so big there's a chance you can find some places where my old code still is unfortunately
- I tried to use as little external libraries as possible, mostly because I didn't want this to end up like some projects where it has to install a million different things. Also fits with the theme of 'making stuff all myself from scratch'.
- This project will be renamed at some point before v4.0.0 releases to Apricot

{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  nativeBuildInputs = (with pkgs; [
    python313
    stdenv.cc.cc.lib
  ]) ++ (with pkgs.python313Packages; [
    pip
    setuptools
    wheel
    debugpy

    tkinter
    pygame
    numpy
    pysdl2
    pillow
    shapely
    pyperclip
    freetype-py
  ]);

  shellHook = ''
    # Because stubgen-pyx doesn't have a nix package, we need to use pip to install it.
    export _LOCAL_PY_PKGS="''${PWD}/.pypkgs"
    export PYTHONPATH="''${_LOCAL_PY_PKGS}:''${PYTHONPATH}"
    mkdir -p "''${_LOCAL_PY_PKGS}"
    if [ ! -f "''${_LOCAL_PY_PKGS}/.gitignore" ]; then
      echo "*" > "''${_LOCAL_PY_PKGS}/.gitignore"
    fi
    python -m pip install --target "''${_LOCAL_PY_PKGS}" stubgen-pyx
  '';
}

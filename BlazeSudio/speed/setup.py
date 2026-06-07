from stubgen_pyx.stubgen import StubgenPyx
from Cython.Build import cythonize
from setuptools import Extension
from setuptools.dist import Distribution
from setuptools.command.build_ext import build_ext
import numpy
import sys
import os

if '-h' in sys.argv or '--help' in sys.argv or len(sys.argv) > 1:
    print("Usage: "+sys.argv[0]+" [-h/--help]")
    exit()

ROOT = os.path.abspath(__file__+"/../../../")
os.chdir(ROOT)
sys.path.append(ROOT)
import BlazeSudio.speed
BlazeSudio.speed._COMPILING = True

print("Generating stubs...")
files = StubgenPyx().convert_glob(ROOT+"/**/*.pyx")
MODULES = []
for f in files:
    pyx_path = f.pyx_file.resolve()
    rel = pyx_path.relative_to(ROOT)
    parts = rel.with_suffix("").parts
    module_name = ".".join(parts)
    MODULES.append((module_name, str(pyx_path)))

if len(MODULES) > 0:
    print(f"Compiling modules: {', '.join(m[0] for m in MODULES)}...")
    if sys.platform == 'win32':
        compile_flags = ['/openmp']
        link_flags = []
    else:
        compile_flags = ['-fopenmp']
        link_flags = ['-fopenmp']
    compile_flags.extend(["-O3", "-ffast-math", "-funroll-loops"])
    extensions = [
        Extension(
            name=modname,
            sources=[src],
            include_dirs=[numpy.get_include()],
            define_macros=[
                ("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION"),
                ("Py_LIMITED_API", "0x030B0000")
            ],
            py_limited_api=True,
            extra_compile_args=compile_flags,
            extra_link_args=link_flags,
        )
        for modname, src in MODULES
    ]
    ext_modules = cythonize(
        extensions,
        nthreads=6,
        language_level="3",
        compiler_directives={'binding': False}
    )

    dist = Distribution({"name": "inline-build", "ext_modules": ext_modules})
    cmd = build_ext(dist)
    cmd.build_lib = os.getcwd()
    cmd.build_temp = os.path.join(os.getcwd(), "build")
    cmd.inplace = True
    cmd.parallel = 6

    cmd.ensure_finalized()
    cmd.run()
else:
    print("No modules found!")

print("Finished!")

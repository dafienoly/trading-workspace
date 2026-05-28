from setuptools import Extension, setup

from Cython.Build import cythonize
import numpy as np

extensions = [
    Extension(
        "chixiao.perf.factor_calculator_fast",
        sources=["src/chixiao/perf/factor_calculator_fast.pyx"],
        include_dirs=[np.get_include()],
    )
]

setup(
    ext_modules=cythonize(extensions, language_level="3"),
)

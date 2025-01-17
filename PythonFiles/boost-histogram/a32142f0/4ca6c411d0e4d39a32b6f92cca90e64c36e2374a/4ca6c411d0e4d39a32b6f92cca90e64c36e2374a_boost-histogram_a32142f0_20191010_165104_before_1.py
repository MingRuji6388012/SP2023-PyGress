from __future__ import division
from setuptools import find_packages
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import setuptools
import sys
import os

# Change to using pathlib when Python2 support is dropped
class Path(str):
    def __truediv__(self, s):
        return self.__class__(os.path.join(self, s))


# Baes directory as a Path
BASE_DIR = Path(os.path.abspath(os.path.dirname(__file__)))

# Official trick to avoid pytest-runner as requirement if not needed
needs_pytest = {"pytest", "test", "ptr"}.intersection(sys.argv)
pytest_runner = ["pytest-runner"] if needs_pytest else []

# Use -j N or set the environment variable NPY_NUM_BUILD_JOBS
try:
    from numpy.distutils.ccompiler import CCompiler_compile
    import distutils.ccompiler

    distutils.ccompiler.CCompiler.compile = CCompiler_compile
except ImportError:
    print("Numpy not found, parallel compile not available")

# Read __version__ into about
about = {}
with open(BASE_DIR / "boost_histogram/version.py") as f:
    exec(f.read(), about)

# Read in readme
with open(BASE_DIR / "README.md", "rb") as f:
    description = f.read().decode("utf8", "ignore")

SRC_FILES = [
    "src/module.cpp",
    "src/register_version.cpp",
    "src/register_algorithm.cpp",
    "src/register_axis.cpp",
    "src/register_shared_histogram.cpp",
    "src/register_general_histograms.cpp",
    "src/register_storage.cpp",
    "src/register_accumulators.cpp",
]

INCLUDE_FILES = [
    "include",
    "extern/assert/include",
    "extern/callable_traits/include",
    "extern/config/include",
    "extern/core/include",
    "extern/histogram/include",
    "extern/mp11/include",
    "extern/pybind11/include",
    "extern/throw_exception/include",
    "extern/variant2/include",
]

ext_modules = [
    Extension(
        "boost_histogram.core",
        [str(BASE_DIR / f) for f in SRC_FILES],
        include_dirs=[str(BASE_DIR / f) for f in INCLUDE_FILES],
        language="c++",
    )
]

# As of Python 3.6, CCompiler has a `has_flag` method.
# cf http://bugs.python.org/issue26689
def has_flag(compiler, flagname):
    """Return a boolean indicating whether a flag name is supported on
    the specified compiler.
    """
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".cpp") as f:
        f.write("int main (int argc, char **argv) { return 0; }")
        try:
            compiler.compile([f.name], extra_postargs=[flagname])
        except setuptools.distutils.errors.CompileError:
            return False
    return True


def cpp_flag(compiler):
    """Return the -std=c++14 compiler flag.
    """
    if has_flag(compiler, "-std=c++14"):
        return "-std=c++14"
    else:
        raise RuntimeError(
            "Unsupported compiler -- at least C++14 support " "is needed!"
        )


class BuildExt(build_ext):
    """A custom build extension for adding compiler-specific options."""

    c_opts = {"msvc": ["/EHsc", "/bigobj"], "unix": []}

    if sys.platform == "darwin":
        c_opts["unix"] += ["-stdlib=libc++", "-mmacosx-version-min=10.9"]

    def build_extensions(self):
        ct = self.compiler.compiler_type
        opts = self.c_opts.get(ct, [])
        if ct == "unix":
            opts.append('-DVERSION_INFO="%s"' % self.distribution.get_version())
            opts.append(cpp_flag(self.compiler))
            if has_flag(self.compiler, "-fvisibility=hidden"):
                opts.append("-fvisibility=hidden")
        elif ct == "msvc":
            opts.append('/DVERSION_INFO=\\"%s\\"' % self.distribution.get_version())
        for ext in self.extensions:
            ext.extra_compile_args = opts
        build_ext.build_extensions(self)


extras = {
    "test": ["pytest", "pytest-benchmark", "numpy", 'futures; python_version < "3"'],
    "docs": ["Sphinx>=2.0.0", "recommonmark>=0.5.0", "sphinx_rtd_theme"],
}

setup(
    name="boost-histogram",
    version=about["__version__"],
    author="Henry Schreiner",
    author_email="hschrein@cern.ch",
    maintainer="Henry Schreiner",
    maintainer_email="hschrein@cern.ch",
    url="https://github.com/scikit-hep/boost-histogram",
    description="The Boost::Histogram Python wrapper.",
    long_description=description,
    long_description_content_type="text/markdown",
    ext_modules=ext_modules,
    packages=find_packages(exclude=["tests"]),
    cmdclass={"build_ext": BuildExt},
    test_suite="tests",
    install_requires=["numpy"],
    tests_require=extras["test"],
    setup_requires=[] + pytest_runner,
    extras_require=extras,
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: C++",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Software Development",
        "Topic :: Utilities",
    ],
)

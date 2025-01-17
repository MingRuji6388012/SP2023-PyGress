from setuptools import setup

__author__ = "Alex Laird"
__copyright__ = "Copyright 2018, Alex Laird"
__version__ = "1.3.3"

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="pyngrok",
    version=__version__,
    packages=["pyngrok"],
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*",
    install_requires=[
        "future",
        "pyyaml"
    ],
    entry_points="""
        [console_scripts]
        ngrok=pyngrok.ngrok:run
    """,
    description="A Python wrapper for Ngrok.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Alex Laird",
    author_email="contact@alexlaird.com",
    url="https://github.com/alexdlaird/pyngrok",
    download_url="https://github.com/alexdlaird/pyngrok/archive/{}.tar.gz".format(__version__),
    keywords=["ngrok", "tunnel", "tunneling", "webhook", "localhost"],
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Operating System :: Unix"
    ]
)

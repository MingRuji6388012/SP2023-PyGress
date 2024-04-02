import os
from setuptools import setup, find_packages
import clog

setup(
    name="clog",
    version=clog.__version__,
    description="pretty-print with color",
    long_description=open(os.path.join("README.md")).read(),
    keywords="debugging, log, color, pretty-print, rich",
    author="Brad Montgomery",
    author_email="brad@bradmontgomery.net",
    url="https://github.com/bradmontgomery/clog",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "rich",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    license="MIT",
    include_package_data=True,
    zip_safe=False,
)
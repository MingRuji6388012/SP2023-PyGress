import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="clog",
    version="0.3.0",
    author="Brad Montgomery",
    author_email="brad@bradmontgomery.net",
    description="pretty-print with color",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bradmontgomery/clog",
    project_urls={
        "Bug Tracker": "https://github.com/bradmontgomery/clog/issues",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
    license="MIT",
    install_requires=[
        "rich",
    ],
)

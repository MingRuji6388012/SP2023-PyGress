import setuptools

setuptools.setup(
    name="asl_list",
    version="0.1",
    url="https://github.com/victor-torres/as_list",

    author="Victor Torres",
    author_email="vpaivatorres@gmail.com",

    description="Returns list, tuple or single element list",
    long_description=open('README.md').read(),

    packages=setuptools.find_packages(),

    install_requires=[],

    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
    ],
)

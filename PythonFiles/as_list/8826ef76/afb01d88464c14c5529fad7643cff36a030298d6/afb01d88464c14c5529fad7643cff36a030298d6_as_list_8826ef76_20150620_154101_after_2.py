import setuptools

setuptools.setup(
    name="as_list",
    version="0.2.1",
    url="https://github.com/victor-torres/as_list",

    author="Victor Torres",
    author_email="vpaivatorres@gmail.com",

    description="Verifies if giving object is list or tuple; if not returns a list with it as single element",

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

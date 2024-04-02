import os
from setuptools import setup, find_packages
import clog

setup(
    name='clog',
    version=clog.__version__,
    description='pretty-printed and colofor logging',
    long_description=open(os.path.join('README.rst')).read(),
    keywords='django, log, color',
    author='Brad Montgomery',
    author_email='brad@bradmontgomery.net',
    url='https://github.com/bradmontgomery/clog',
    packages=find_packages(),
    classifiers=[
        'Framework :: Django',
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    license='MIT',
    include_package_data=True,
    zip_safe=False,
    install_requires=['Django>=1.4.1'],
)

import os
from setuptools import setup, find_packages
import clog

setup(
    name='clog',
    version=clog.__version__,
    description='pretty-printed and colofor logging',
    long_description=open(os.path.join('README.rst')).read(),
    keywords='debugging, log, color',
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
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    license='MIT',
    include_package_data=True,
    zip_safe=False,
)

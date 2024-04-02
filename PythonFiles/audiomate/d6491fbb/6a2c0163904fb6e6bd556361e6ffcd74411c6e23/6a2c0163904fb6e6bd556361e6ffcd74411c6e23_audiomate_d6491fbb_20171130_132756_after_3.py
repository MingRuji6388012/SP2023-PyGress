from setuptools import find_packages
from setuptools import setup

setup(name='pingu',
      version='0.1',
      description='Handling of audio datasets/corpora.',
      url='',
      author='Matthias Buechi',
      author_email='buec@zhaw.ch',
      classifiers=[
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3 :: Only',
          'Topic :: Scientific/Engineering :: Human Machine Interfaces'
      ],
      keywords='',
      license='MIT',
      packages=find_packages(),
      install_requires=[
          'numpy==1.13.3',
          'scipy==1.0.0',
          'librosa==0.5.1',
          'h5py==2.7.1'
      ],
      include_package_data=True,
      zip_safe=False,
      test_suite='nose.collector',
      extras_require={
          'test': ['nose==1.3.7'],
          'docs': ['Sphinx==1.6.5', 'sphinx-rtd-theme==0.2.5b1']
      },
      entry_points={
      }
      )
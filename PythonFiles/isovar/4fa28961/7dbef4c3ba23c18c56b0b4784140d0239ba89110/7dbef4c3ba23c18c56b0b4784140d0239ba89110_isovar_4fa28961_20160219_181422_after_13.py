# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import (absolute_import,)

import os
import logging

from setuptools import setup

readme_dir = os.path.dirname(__file__)
readme_filename = os.path.join(readme_dir, 'README.md')

try:
    with open(readme_filename, 'r') as f:
        readme = f.read()
except:
    logging.warn("Failed to load %s" % readme_filename)
    readme = ""

try:
    import pypandoc
    readme = pypandoc.convert(readme, to='rst', format='md')
except:
    logging.warn("Conversion of long_description from MD to RST failed")
    pass

if __name__ == '__main__':
    setup(
        name='isovar',
        version="0.0.1",
        description="Assemble transcript sequences fragments near variants",
        author="Alex Rubinsteyn and Arman Aksoy",
        author_email="alex {dot} rubinsteyn {at} mssm {dot} edu",
        url="https://github.com/hammerlab/isovar",
        license="http://www.apache.org/licenses/LICENSE-2.0.html",
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Environment :: Console',
            'Operating System :: OS Independent',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: Apache Software License',
            'Programming Language :: Python',
            'Topic :: Scientific/Engineering :: Bio-Informatics',
        ],
        install_requires=[
            'six',
            'pysam >= 0.8.4'
        ],

        long_description=readme,
        packages=['isovar'],
        scripts=[
            "script/isovar-find-matching-transcripts.py",
            "script/isovar-translate-all-frames.py",
            "script/isovar-translate-variants.py",
        ],
    )

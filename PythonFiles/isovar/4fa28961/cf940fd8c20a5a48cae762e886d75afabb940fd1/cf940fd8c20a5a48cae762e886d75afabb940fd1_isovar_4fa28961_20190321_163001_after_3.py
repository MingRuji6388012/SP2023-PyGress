# Copyright (c) 2016-2019. Mount Sinai School of Medicine
#
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

from __future__ import print_function, division, absolute_import

from collections import defaultdict
import numpy as np

def list_to_string(list_of_anything, sep=";"):
    """
    Helper function used for building the fields of a printable dataframe
    """
    return sep.join(str(x) for x in list_of_anything)


def groupby(xs, key_fn):
    """
    Group elements of the list `xs` by keys generated from calling `key_fn`.

    Returns a dictionary which maps keys to sub-lists of `xs`.
    """
    result = defaultdict(list)
    for x in xs:
        key = key_fn(x)
        result[key].append(x)
    return result

def safediv(x, y):
    """
    Compute ratio between two fields safely, so that
    if numerator is zero, result is zero and if denominator
    is zero then result is infinity.

    Parameters
    ----------
    x : int or float
        Numerator value

    y : int or float
        Denominator value

    Returns float
    """
    if x == 0:
        return 0.0
    elif y == 0:
        return np.inf
    else:
        return x / y

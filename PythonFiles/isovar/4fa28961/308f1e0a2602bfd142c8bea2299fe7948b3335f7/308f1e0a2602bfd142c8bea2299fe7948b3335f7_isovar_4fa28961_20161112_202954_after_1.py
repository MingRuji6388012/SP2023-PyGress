# Copyright (c) 2016. Mount Sinai School of Medicine
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

dna_complement_dictionary = {
    "A": "T",
    "T": "A",
    "C": "G",
    "G": "C",
}

dna_nucleotides = list(sorted(dna_complement_dictionary.keys()))

dna_nucleotide_to_index = {c: i for (i, c) in enumerate(dna_nucleotides)}

index_to_dna_nucleotide = {i: c for (i, c) in enumerate(dna_nucleotides)}

def complement_dna(seq):
    return "".join(dna_complement_dictionary[nt] for nt in seq)

def reverse_complement_dna(seq):
    return complement_dna(seq)[::-1]

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

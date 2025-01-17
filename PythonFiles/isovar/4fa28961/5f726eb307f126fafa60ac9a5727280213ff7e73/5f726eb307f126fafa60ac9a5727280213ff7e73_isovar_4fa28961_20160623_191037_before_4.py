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

import numpy as np

from .common import (
    make_prefix_suffix_pairs,
    nucleotide_to_index,
    index_to_nucleotide,
)

def nucleotide_counts(partitioned_read_sequences):
    """
    Count the number of times {A, C, T, G} occur at each position to the
    left and right of the variant.

    Parameters
    ----------
    partitioned_read_sequences : list of tuples
        Each tuple has three elements:
            - sequence before mutant nucleotides
            - mutant nucleotides
            - sequence after mutant nucleotides

    Returns a tuple with the following elements:
        - a matrix with four rows and as many columns as the sum of the longest
          prefix preceding the variant, the longest suffix after the variant and
          the number of variant nucleotids.
        - the column indices for the variant nucleotides
    """
    variant_seq, prefix_suffix_pairs = make_prefix_suffix_pairs(
        partitioned_read_sequences)
    n_reads = len(prefix_suffix_pairs)
    max_prefix_length = max(len(p) for (p, _) in prefix_suffix_pairs)
    max_suffix_length = max(len(s) for (_, s) in prefix_suffix_pairs)
    n_variant_nucleotides = len(variant_seq)

    n_cols = max_prefix_length + max_suffix_length + n_variant_nucleotides

    counts = np.zeros((4, n_cols), dtype=int)

    variant_column_indices = []

    # first fill in the variant nucleotide counts, since they'll
    # be invariant across all the supporting reads
    for i, nucleotide in enumerate(variant_seq):
        variant_col_idx = max_prefix_length + i
        variant_column_indices.append(variant_col_idx)
        row_idx = nucleotide_to_index[nucleotide_to_index]
        counts[row_idx, variant_col_idx] = n_reads

    for p, s in prefix_suffix_pairs:
        for i, prefix_col_idx in enumerate(range(
                max_prefix_length - len(p),
                max_prefix_length)):
            row_idx = nucleotide_to_index[p[i]]
            counts[row_idx, prefix_col_idx] += 1
        for i, suffix_col_idx in enumerate(range(
                max_prefix_length + n_variant_nucleotides,
                max_prefix_length + n_variant_nucleotides + len(s))):
            row_idx = nucleotide_to_index[s[i]]
            counts[row_idx, suffix_col_idx] += 1
    return counts, variant_column_indices

def most_common_nucleotides(partitioned_read_sequences):
    """
    Find the most common nucleotide at each offset to the left and
    right of a variant.

    Parameters
    ----------
    partitioned_read_sequences : list of tuples
        Each tuple has three elements:
            - sequence before mutant nucleotides
            - mutant nucleotides
            - sequence after mutant nucleotides

    Returns a tuple with the following elements:
        - nucleotide sequence from most common nucleotide at each offset
           relative to the variant
        - an array of counts indicating how many reads supported this nucleotide
        - an array of counts for all the *other* nucleotides at that position
    """
    counts, variant_column_indices = nucleotide_counts(
        partitioned_read_sequences)
    max_count_per_column = counts.max(axis=0)

    assert len(max_count_per_column) == counts.shape[1]
    max_nucleotide_index_per_column = np.argmax(counts, axis=0)
    assert len(max_nucleotide_index_per_column) == counts.shape[1]
    nucleotides = [
        index_to_nucleotide[idx]
        for idx in max_nucleotide_index_per_column
    ]
    other_nucleotide_counts = counts.sum(axis=0) - max_count_per_column
    return "".join(nucleotides), max_count_per_column, other_nucleotide_counts

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

"""
Functions for filtering, grouping, and summarizing collections of
AlleleRead objects.
"""

from collections import defaultdict

from .common import groupby
from .logging import get_logger
from .variant_helpers import trim_variant

logger = get_logger(__name__)


def group_reads_by_allele(allele_reads):
    """
    Returns dictionary mapping each allele's nucleotide sequence to a list of
    supporting AlleleRead objects.
    """
    allele_to_reads_dict = defaultdict(list)
    for allele_read in allele_reads:
        allele_to_reads_dict[allele_read.allele].append(allele_read)
    return allele_to_reads_dict


def filter_non_alt_reads_for_variant(variant, allele_reads):
    """
    Given a variant and an unfiltered collection of AlleleRead objects,
    return only the AlleleRead object which match the alt allele of the variant.
    """
    _, _, alt = trim_variant(variant)
    return [read for read in allele_reads if read.allele == alt]


def filter_non_alt_reads_for_variants(variants_and_allele_reads_sequence):
    """
    Given a sequence of variants paired with all of their overlapping reads,
    yields a sequence of variants paired only with reads which contain their
    mutated nucleotide sequence.
    """
    for variant, allele_reads in variants_and_allele_reads_sequence:
        yield variant, filter_non_alt_reads_for_variant(variant, allele_reads)


def get_single_allele_from_reads(allele_reads):
    """
    Given a sequence of AlleleRead objects, which are expected to all have
    the same allele, return that allele.
    """
    allele_reads = list(allele_reads)

    if len(allele_reads) == 0:
        raise ValueError("Expected non-empty list of AlleleRead objects")

    seq = allele_reads[0].allele
    if any(read.allele != seq for read in allele_reads):
        raise ValueError("Expected all AlleleRead objects to have same allele '%s', got %s" % (
            seq, allele_reads))
    return seq


def group_unique_sequences(
        allele_reads,
        max_prefix_size=None,
        max_suffix_size=None):
    """
    Given a list of AlleleRead objects, extracts all unique
    (prefix, allele, suffix) sequences and associate each with a list
    of reads that contained that sequence.
    """
    groups = defaultdict(set)
    for r in allele_reads:
        prefix = r.prefix
        allele = r.allele
        suffix = r.suffix
        if max_prefix_size and len(prefix) > max_prefix_size:
            prefix = prefix[-max_prefix_size:]
        if max_suffix_size and len(suffix) > max_suffix_size:
            suffix = suffix[:max_suffix_size]
        key = (prefix, allele, suffix)
        groups[key].add(r)
    return groups


def count_unique_sequences(
        allele_reads,
        max_prefix_size=None,
        max_suffix_size=None):
    """
    Given a list of AlleleRead objects, extracts all unique
    (prefix, allele, suffix) sequences and associate each with the number
    of reads that contain that sequence.
    """
    groups = group_unique_sequences(
        allele_reads,
        max_prefix_size=max_prefix_size,
        max_suffix_size=max_suffix_size)
    return {
        seq_tuple: len(read_names)
        for (seq_tuple, read_names) in groups.items()
    }


def group_reads_by_allele(allele_reads):
    """
    Returns dictionary mapping each allele's nucleotide sequence to a list of
    supporting AlleleRead objects.
    """
    return groupby(allele_reads, lambda read: read.allele)

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

from isovar.reference_context import (
    sequence_key_for_variant_on_transcript,
    SequenceKey,
)
from varcode import Variant
from pyensembl import ensembl_grch38
from nose.tools import eq_


def _check_equal_fields(result, expected):
    """
    Assert that fields of two SequenceKey objects have
    same field values.
    """
    for field in SequenceKey._fields:
        result_value = getattr(result, field)
        expected_value = getattr(expected, field)
        assert result_value == expected_value, \
            "Wrong value for '%s', expected %s but got %s" % (
                field,
                expected_value,
                result_value)

def test_sequence_key_for_variant_on_transcript_substitution():
    # rs769125639 is a simple T>A substitution in the 6th nucleotide of
    # BRCA2-001's 5' UTR
    brca2_variant_rs769125639 = Variant(
        "13", 32315479, "T", "A", ensembl_grch38)
    brca2_001 = ensembl_grch38.transcripts_by_name("BRCA2-001")[0]
    # first 50 characters of BRCA2-001:
    #  "GGGCTTGTGGCGCGAGCTTCTGAAACTAGGCGGCAGAGGCGGAGCCGCTG"
    brca2_ref_seq = brca2_001.sequence[:50]
    eq_(brca2_ref_seq, "GGGCTTGTGGCGCGAGCTTCTGAAACTAGGCGGCAGAGGCGGAGCCGCTG")
    print(brca2_ref_seq)
    # get the 5 nucleotides before the variant and 10 nucleotides after
    sequence_key = sequence_key_for_variant_on_transcript(
        variant=brca2_variant_rs769125639,
        transcript=brca2_001,
        context_size=10)
    expected_sequence_key = SequenceKey(
        strand="+",
        sequence_before_variant_locus=brca2_ref_seq[:5],
        sequence_at_variant_locus="T",
        sequence_after_variant_locus=brca2_ref_seq[6:16])
    _check_equal_fields(sequence_key, expected_sequence_key)


def test_sequence_key_for_variant_on_transcript_deletion():
    # Delete the 6th nucleotide of BRCA2-001's 5' UTR
    brca2_variant_deletion = Variant(
        "13", 32315479, "T", "", ensembl_grch38)
    brca2_001 = ensembl_grch38.transcripts_by_name("BRCA2-001")[0]
    # first 50 characters of BRCA2-001:
    #  "GGGCTTGTGGCGCGAGCTTCTGAAACTAGGCGGCAGAGGCGGAGCCGCTG"
    brca2_ref_seq = brca2_001.sequence[:50]
    eq_(brca2_ref_seq, "GGGCTTGTGGCGCGAGCTTCTGAAACTAGGCGGCAGAGGCGGAGCCGCTG")
    print(brca2_ref_seq)
    # get the 5 nucleotides before the variant and 10 nucleotides after
    sequence_key = sequence_key_for_variant_on_transcript(
        variant=brca2_variant_deletion,
        transcript=brca2_001,
        context_size=10)
    expected_sequence_key = SequenceKey(
        strand="+",
        sequence_before_variant_locus=brca2_ref_seq[:5],
        sequence_at_variant_locus="T",
        sequence_after_variant_locus=brca2_ref_seq[6:16])
    _check_equal_fields(sequence_key, expected_sequence_key)

def test_sequence_key_for_variant_on_transcript_insertion():
    # Insert 'CCC' after the 6th nucleotide of BRCA2-001's 5' UTR
    brca2_variant_insertion = Variant(
        "13", 32315479, "T", "TCCC", ensembl_grch38)
    brca2_001 = ensembl_grch38.transcripts_by_name("BRCA2-001")[0]
    # first 50 characters of BRCA2-001:
    #  "GGGCTTGTGGCGCGAGCTTCTGAAACTAGGCGGCAGAGGCGGAGCCGCTG"
    brca2_ref_seq = brca2_001.sequence[:50]
    eq_(brca2_ref_seq, "GGGCTTGTGGCGCGAGCTTCTGAAACTAGGCGGCAGAGGCGGAGCCGCTG")
    print(brca2_ref_seq)
    # get the 5 nucleotides before the variant and 10 nucleotides after
    sequence_key = sequence_key_for_variant_on_transcript(
        variant=brca2_variant_insertion,
        transcript=brca2_001,
        context_size=10)

    # expecting nothing at the variant locus since we're inserting between
    # two reference nucleotides
    expected_sequence_key = SequenceKey(
        strand="+",
        sequence_before_variant_locus=brca2_ref_seq[:6],
        sequence_at_variant_locus="",
        sequence_after_variant_locus=brca2_ref_seq[6:16])
    _check_equal_fields(sequence_key, expected_sequence_key)


def test_sequence_key_for_variant_on_transcript_substitution_reverse_strand():
    # Replace start codon of TP53-001 with 'CCC', however since this is on
    # reverse strand the variant becomes "CAT">"GGG"
    tp53_substitution = Variant(
        "17", 7676592, "CAT", "GGG", ensembl_grch38)
    tp53_001 = ensembl_grch38.transcripts_by_name("TP53-001")[0]
    # Sequence of TP53 around start codon with 10 context nucleotides:
    # In [51]: t.sequence[190-10:190+13]
    # Out[51]: 'GGTCACTGCC_ATG_GAGGAGCCGC'
    eq_(tp53_001.sequence[190 - 10:190 + 13], "GGTCACTGCCATGGAGGAGCCGC")

    # get the 5 nucleotides before the variant and 10 nucleotides after
    sequence_key = sequence_key_for_variant_on_transcript(
        variant=tp53_substitution,
        transcript=tp53_001,
        context_size=10)

    expected_sequence_key = SequenceKey(
        strand="-",
        sequence_before_variant_locus="GGTCACTGCC",
        sequence_at_variant_locus="ATG",
        sequence_after_variant_locus="GAGGAGCCGC")
    _check_equal_fields(sequence_key, expected_sequence_key)

def test_sequence_key_for_variant_on_transcript_deletion_reverse_strand():
    # delete start codon of TP53-001, which in reverse complement means
    # deleting the sequence "CAT"
    tp53_deletion = Variant(
        "17", 7676592, "CAT", "", ensembl_grch38)
    tp53_001 = ensembl_grch38.transcripts_by_name("TP53-001")[0]
    # Sequence of TP53 around start codon with 10 context nucleotides:
    # In [51]: t.sequence[190-10:190+13]
    # Out[51]: 'GGTCACTGCC_ATG_GAGGAGCCGC'
    eq_(tp53_001.sequence[190 - 10:190 + 13], "GGTCACTGCCATGGAGGAGCCGC")

    # get the 5 nucleotides before the variant and 10 nucleotides after
    sequence_key = sequence_key_for_variant_on_transcript(
        variant=tp53_deletion,
        transcript=tp53_001,
        context_size=10)

    expected_sequence_key = SequenceKey(
        strand="-",
        sequence_before_variant_locus="GGTCACTGCC",
        sequence_at_variant_locus="ATG",
        sequence_after_variant_locus="GAGGAGCCGC")
    _check_equal_fields(sequence_key, expected_sequence_key)

def test_sequence_key_for_variant_on_transcript_insertion_reverse_strand():
    # insert 'CCC' after start codon of TP53-001, which on the reverse
    # complement means inserting "GGG" between "CTC_CAT"
    tp53_insertion = Variant(
        "17", 7676589, "CTC", "CTCGGG", ensembl_grch38)
    tp53_001 = ensembl_grch38.transcripts_by_name("TP53-001")[0]
    # Sequence of TP53 around start codon with 10 context nucleotides:
    # In [51]: t.sequence[190-10:190+13]
    # Out[51]: 'GGTCACTGCC_ATG_GAGGAGCCGC'
    eq_(tp53_001.sequence[190 - 10:190 + 13], "GGTCACTGCCATGGAGGAGCCGC")

    # The above gives us the cDNA sequence from the transcript, whereas the
    # reverse complement genomic sequence is:
    #    GCGGCTCCTC_CAT_GGCAGTGACC

    # get the 5 nucleotides before the variant and 10 nucleotides after
    sequence_key = sequence_key_for_variant_on_transcript(
        variant=tp53_insertion,
        transcript=tp53_001,
        context_size=10)

    expected_sequence_key = SequenceKey(
        strand="-",
        sequence_before_variant_locus="CACTGCCATG",
        sequence_at_variant_locus="",
        sequence_after_variant_locus="GAGGAGCCGC")
    _check_equal_fields(sequence_key, expected_sequence_key)

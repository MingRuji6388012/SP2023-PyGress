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

from isovar.variant_reads import reads_supporting_variant
from isovar.variant_sequences import (
    initial_variant_sequences_from_reads,
    VariantSequence
)
from isovar.allele_reads import AlleleRead
from isovar.assembly import (
    iterative_overlap_assembly,
    greedy_merge,
    collapse_substrings
)

from pyensembl import ensembl_grch38
from varcode import Variant
from nose.tools import eq_

from testing_helpers import load_bam

def test_assemble_transcript_fragments_snv():
    samfile = load_bam("data/cancer-wgs-primary.chr12.bam")
    chromosome = "chr12"
    base1_location = 65857041
    ref = "G"
    alt = "C"
    variant = Variant(
        contig=chromosome,
        start=base1_location,
        ref=ref,
        alt=alt,
        ensembl=ensembl_grch38)
    variant_reads = reads_supporting_variant(
        variant=variant,
        samfile=samfile,
        chromosome=chromosome,)

    sequences = iterative_overlap_assembly(
        initial_variant_sequences_from_reads(variant_reads),
        min_overlap_size=30)

    assert len(sequences) > 0
    max_read_length = max(len(r) for r in variant_reads)
    for s in sequences:
        print("%s%s%s weight=%d length=%d" % (
            s.prefix,
            s.alt,
            s.suffix,
            len(s.reads),
            len(s.sequence)))
        eq_(s.alt, alt)
        if len(s.read_names) > 1:
            # expect sequences supported by more than one read to be greater
            # than the read length
            assert len(s) > max_read_length, \
                "Expected assembled sequences to be longer than read length (%d)" % (
                    max_read_length,)

def test_assembly_of_simple_sequence_from_mock_reads():
    # Read sequences:
    #    AAAAA|CC|TTTTT
    #    AAAAA|CC|TTTTT
    #   GAAAAA|CC|TTTTTG
    #     AAAA|CC|TTTT
    reads = [
        # two identical reads with sequence AAAAA|CC|TTTTT
        AlleleRead(prefix="A" * 5, allele="CC", suffix="T" * 5, name="dup1"),
        AlleleRead(prefix="A" * 5, allele="CC", suffix="T" * 5, name="dup2"),
        # longer sequence GAAAAA|CC|TTTTTG
        AlleleRead(
            prefix="G" + "A" * 5,
            allele="CC",
            suffix="T" * 5 + "G",
            name="longer"),
        # shorter sequence AAAA|CC|TTTT
        AlleleRead(prefix="A" * 4, allele="CC", suffix="T" * 4, name="shorter"),
    ]
    expected_variant_sequence = VariantSequence(
        prefix="G" + "A" * 5, alt="CC", suffix="T" * 5 + "G", reads=reads)
    initial_variant_sequences = initial_variant_sequences_from_reads(reads)
    # expecting one fewer sequence than reads since two of the reads are
    # duplicates
    eq_(len(initial_variant_sequences), len(reads) - 1)

    # calling into either iterative_overlap_assembly or greedy_merge should
    # give same results
    for fn in [iterative_overlap_assembly, greedy_merge]:

        assembled_variant_sequences = fn(
            initial_variant_sequences,
            min_overlap_size=1)

        # since no reads contradict each other then we should get back a single
        # assembled sequence
        eq_(len(assembled_variant_sequences),
            1,
            "Unexpected number of variant sequences: %s" % (assembled_variant_sequences,))
        assembled_variant_sequence = assembled_variant_sequences[0]
        eq_(assembled_variant_sequence, expected_variant_sequence)

        eq_(len(assembled_variant_sequence.reads), len(reads))

        eq_(assembled_variant_sequence.min_coverage(), 1)
        # 2 bases with 1/4 reads, 2 bases with 3/4 reads, remaining 10 bases with
        # all 4/4 reads
        expected_mean_coverage = (2 * 1 + 2 * 3 + 10 * 4) / 14
        eq_(assembled_variant_sequence.mean_coverage(), expected_mean_coverage)

def test_collapse_substrings():
    # AAA|C|GGG
    vs_longer = VariantSequence(
        prefix="AAA", alt="C", suffix="GGG", reads={"1"})
    # AAA|C|GG
    vs_shorter = VariantSequence(
        prefix="AAA", alt="C", suffix="GG", reads={"2"})
    vs_unrelated = VariantSequence("TAA", alt="C", suffix="GG", reads={"3"})
    results = collapse_substrings([vs_longer, vs_shorter, vs_unrelated])
    eq_(len(results), 2), "Expected two sequences, got %d: %s" % (
        len(results), results)
    vs_combined = vs_longer.add_reads({"2"})
    assert vs_combined in results, "Expeceted %s to be in %s" % (vs_combined, results)
    assert vs_unrelated in results, "Expected %s to be in %s" % (vs_unrelated, results)

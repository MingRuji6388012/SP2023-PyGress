from __future__ import print_function, division, absolute_import

from isovar.nucleotide_counts import most_common_nucleotides
from isovar.allele_read_helpers import reads_supporting_variant

from varcode import Variant
from pyensembl import ensembl_grch38
from nose.tools import eq_

from testing_helpers import load_bam


def test_most_common_nucleotides_for_chr12_deletion():
    samfile = load_bam("data/cancer-wgs-primary.chr12.bam")
    chromosome = "chr12"
    base1_location = 70091490
    ref = "TTGTAGATGCTGCCTCTCC"
    alt = ""
    variant = Variant(
        chromosome,
        base1_location,
        ref,
        alt,
        ensembl=ensembl_grch38)
    variant_reads = reads_supporting_variant(
        samfile=samfile,
        chromosome=chromosome,
        variant=variant)
    consensus_sequence, chosen_counts, other_counts = most_common_nucleotides(
        variant_reads)
    print(chosen_counts)
    print(other_counts)
    eq_(len(chosen_counts), len(consensus_sequence))
    eq_(len(other_counts), len(consensus_sequence))
    assert other_counts.sum() < chosen_counts.sum(), \
        "Counts for alternate nucleotides should not exceed the chosen sequence"

    number_matching_reads = 0
    for variant_read in variant_reads:
        full_seq = variant_read.prefix + variant_read.allele + variant_read.suffix
        number_matching_reads += (full_seq in consensus_sequence)
    fraction_matching_reads = number_matching_reads / float(len(variant_reads))
    print("Fraction matching reads is %d/%d = %f" % (
        number_matching_reads, len(variant_reads), fraction_matching_reads))
    assert fraction_matching_reads > 0.5, \
        "Expected majority of reads to match consensus sequence"

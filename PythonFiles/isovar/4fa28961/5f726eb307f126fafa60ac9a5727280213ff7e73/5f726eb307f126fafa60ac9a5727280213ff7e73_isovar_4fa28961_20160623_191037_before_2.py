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

"""
Reads overlapping a locus of interest split into prefix,
allele (ref, alt, or otherwise), and suffix portions
"""

from __future__ import print_function, division, absolute_import
from collections import namedtuple
import logging

from .locus_read import locus_read_generator
from .default_parameters import (
    MIN_READ_MAPPING_QUALITY,
    USE_SECONDARY_ALIGNMENTS,
    USE_DUPLICATE_READS,
)
from .variant_helpers import trim_variant
from .dataframe_builder import DataFrameBuilder
from .string_helpers import convert_from_bytes_if_necessary, trim_N_nucleotides


# simplified representation of a RNA read containing just the
# sequence before, at, and after the variant locus, along with the read name
AlleleRead = namedtuple(
    "AlleleRead",
    "prefix allele suffix name")


def allele_read_from_locus_read(read_at_locus, n_ref):
    """
    Given a single ReadAtLocus object, return either an AlleleRead or None

    Parameters
    ----------
    read : ReadAtLocus
        Read which may possibly contain the alternate nucleotides

    n_ref : int
        Number of reference positions we are expecting to be modified or
        deleted (for insertions this should be 0)
    """
    sequence = read_at_locus.sequence
    reference_positions = read_at_locus.reference_positions

    # positions of the nucleotides before and after the variant within
    # the read sequence
    read_pos_before = read_at_locus.base0_read_position_before_variant
    read_pos_after = read_at_locus.base0_read_position_after_variant

    # positions of the nucleotides before and after the variant on the
    # reference genome
    ref_pos_before = reference_positions[read_pos_before]

    if ref_pos_before is None:
        logging.warn(
            "Missing reference pos for nucleotide before variant on read: %s" % (
                read_at_locus,))
        return None

    ref_pos_after = reference_positions[read_pos_after]

    if ref_pos_after is None:
        logging.warn(
            "Missing reference pos for nucleotide after variant on read: %s" % (
                read_at_locus,))
        return None

    if n_ref == 0:
        if ref_pos_after - ref_pos_before != 1:
            # if the number of nucleotides skipped isn't the same
            # as the number of reference nucleotides in the variant then
            # don't use this read
            logging.debug(
                "Positions before (%d) and after (%d) variant should be adjacent on read %s" % (
                    ref_pos_before,
                    ref_pos_after,
                    read_at_locus))
            return None

        # insertions require a sequence of non-aligned bases
        # followed by the subsequence reference position
        ref_positions_for_inserted = reference_positions[
            read_pos_before + 1:read_pos_after]
        if any(insert_pos is not None for insert_pos in ref_positions_for_inserted):
            # all these inserted nucleotides should *not* align to the
            # reference
            logging.debug(
                "Skipping read, inserted nucleotides shouldn't map to reference")
            return None
    else:
        # substitutions and deletions
        if ref_pos_after - ref_pos_before != n_ref + 1:
            # if the number of nucleotides skipped isn't the same
            # as the number of reference nucleotides in the variant then
            # don't use this read
            logging.debug(
                "Positions before (%d) and after (%d) variant should be adjacent on read %s" % (
                    ref_pos_before,
                    ref_pos_after,
                    read_at_locus))
            return None

    nucleotides_at_variant_locus = sequence[read_pos_before + 1:read_pos_after]

    prefix = sequence[:read_pos_before + 1]
    suffix = sequence[read_pos_after:]

    prefix, suffix = convert_from_bytes_if_necessary(prefix, suffix)
    prefix, suffix = trim_N_nucleotides(prefix, suffix)

    return AlleleRead(
        prefix,
        nucleotides_at_variant_locus,
        suffix,
        name=read_at_locus.name)

def allele_reads_from_locus_reads(locus_reads, n_ref):
    """
    Given a collection of ReadAtLocus objects, returns a
    list of VariantRead objects (which are split into prefix/variant/suffix
    nucleotides).

    Parameters
    ----------
    locus_reads : sequence of LocusRead records

    n_ref : int
        Number of reference nucleotides affected by variant.

    Generates AlleleRead objects.
    """

    for locus_read in locus_reads:
        allele_read = allele_read_from_locus_read(locus_read, n_ref)
        if allele_read is None:
            continue
        else:
            yield allele_read

def allele_reads_for_variant(
        samfile,
        variant,
        chromosome=None,
        use_duplicate_reads=USE_DUPLICATE_READS,
        use_secondary_alignments=USE_SECONDARY_ALIGNMENTS,
        min_mapping_quality=MIN_READ_MAPPING_QUALITY,
        only_alt_allele=False):
    """
    Find reads in the given SAM/BAM file which overlap the given variant, filter
    to only include those which agree with the variant's nucleotide(s), and turn
    them into a list of VariantRead objects.

    Parameters
    ----------
    samfile : pysam.AlignmentFile

    variant : varcode.Variant

    chromosome : str

    use_duplicate_reads : bool
        Should we use reads that have been marked as PCR duplicates

    use_secondary_alignments : bool
        Should we use reads at locations other than their best alignment

    min_mapping_quality : int
        Drop reads below this mapping quality

    only_alt_allele : bool
        Filter reads to only include those that support the alt allele of
        the variant.

    Returns sequence of AlleleRead objects.
    """
    logging.info("Gathering reads for %s" % variant)
    if chromosome is None:
        chromosome = variant.contig

    logging.info("Gathering variant reads for variant %s (chromosome=%s)" % (
        variant,
        chromosome))

    base1_position, ref, alt = trim_variant(variant)

    if len(ref) == 0:
        # if the variant is an insertion
        base1_position_before_variant = base1_position
        base1_position_after_variant = base1_position + 1
    else:
        base1_position_before_variant = base1_position - 1
        base1_position_after_variant = base1_position + len(ref)

    locus_reads = locus_read_generator(
        samfile=samfile,
        chromosome=chromosome,
        base1_position_before_variant=base1_position_before_variant,
        base1_position_after_variant=base1_position_after_variant,
        use_duplicate_reads=use_duplicate_reads,
        use_secondary_alignments=use_secondary_alignments,
        min_mapping_quality=min_mapping_quality)

    allele_reads = allele_reads_from_locus_reads(
        locus_reads=locus_reads,
        n_ref=len(ref))

    return allele_reads


def allele_reads_for_variants(
        variants,
        samfile,
        use_duplicate_reads=USE_DUPLICATE_READS,
        use_secondary_alignments=USE_SECONDARY_ALIGNMENTS,
        min_mapping_quality=MIN_READ_MAPPING_QUALITY):
    """
    Generates sequence of tuples, each containing a variant paired with
    a list of AlleleRead objects.

    Parameters
    ----------
    variants : varcode.VariantCollection

    samfile : pysam.AlignmentFile

    use_duplicate_reads : bool
        Should we use reads that have been marked as PCR duplicates

    use_secondary_alignments : bool
        Should we use reads at locations other than their best alignment

    min_mapping_quality : int
        Drop reads below this mapping quality
    """
    chromosome_names = set(samfile.references)
    for variant in variants:
        # I imagine the conversation went like this:
        # A: "Hey, I have an awesome idea"
        # B: "What's up?"
        # A: "Let's make two nearly identical reference genomes"
        # B: "But...that sounds like it might confuse people."
        # A: "Nah, it's cool, we'll give the chromosomes different prefixes!"
        # B: "OK, sounds like a good idea."
        if variant.contig in chromosome_names:
            chromosome = variant.contig
        elif "chr" + variant.contig in chromosome_names:
            chromosome = "chr" + variant.contig
        else:
            logging.warn(
                "Chromosome '%s' from variant %s not in alignment file %s" % (
                    chromosome, variant, samfile.filename))
            continue
        allele_reads = allele_reads_for_variant(
            samfile=samfile,
            chromosome=chromosome,
            variant=variant,
            use_duplicate_reads=use_duplicate_reads,
            use_secondary_alignments=use_secondary_alignments,
            min_mapping_quality=min_mapping_quality)
        yield variant, allele_reads

def allele_reads_to_dataframe(variants_and_allele_reads):
    """
    Parameters
    ----------
    variants_and_allele_reads : sequence
        List or generator of pairs whose first element is a Variant and
        whose second element is a sequence of AlleleRead objects.
    """
    df_builder = DataFrameBuilder(AlleleRead)
    for variant, allele_reads in variants_and_allele_reads:
        df_builder.add_many(variant, allele_reads)
    return df_builder.to_dataframe()

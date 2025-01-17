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
This module wraps pysam and gives us a view of any reads overlapping
a variant locus which includes offsets into the read sequence & qualities
for extracting variant nucleotides.
"""

from __future__ import print_function, division, absolute_import
from collections import namedtuple
import logging

from .default_parameters import (
    MIN_READ_MAPPING_QUALITY,
    USE_DUPLICATE_READS,
    USE_SECONDARY_ALIGNMENTS,
)


ReadAtLocus = namedtuple(
    "ReadAtLocus",
    [
        "name",
        "sequence",
        "reference_positions",
        "quality_scores",
        "base0_read_position_before_variant",
        "base0_read_position_after_variant",
    ])


def gather_reads_at_locus(
        samfile,
        chromosome,
        base1_position_before_variant,
        base1_position_after_variant,
        use_duplicate_reads=USE_DUPLICATE_READS,
        use_secondary_alignments=USE_SECONDARY_ALIGNMENTS,
        min_mapping_quality=MIN_READ_MAPPING_QUALITY):
    """
    Generator that yields a sequence of ReadAtLocus records for reads which
    contain the positions before and after a variant. The actual work to figure
    out if what's between those positions matches a variant happens later in
    the `variant_reads` module.

    Parameters
    ----------
    samfile : pysam.AlignmentFile

    chromosome : str

    base1_position_before_variant : int
        Genomic position of reference nucleotide before a variant

    base1_position_after_variant : int
        Genomic position of reference nucleotide before a variant

    use_duplicate_reads : bool
        By default, we're ignoring any duplicate reads

    use_secondary_alignments : bool
        By default we are using secondary alignments, set this to False to
        only use primary alignments of reads.

    min_mapping_quality : int
        Drop reads below this mapping quality

    Yields ReadAtLocus objects
    """
    logging.info(
        "Gathering reads at locus %s: %d-%d" % (
            chromosome,
            base1_position_before_variant,
            base1_position_after_variant))
    base0_position_before_variant = base1_position_before_variant - 1
    base0_position_after_variant = base1_position_after_variant - 1

    # Let pysam pileup the reads covering our location of interest for us
    #
    # We get a pileup at the base before the variant and then check to make sure
    # that reads also overlap the reference position after the variant.
    #
    # Annoyingly AlignmentFile.pileup takes base-0 intervals but returns
    # columns with base-1 positions.
    for column in samfile.pileup(
            chromosome,
            base0_position_before_variant,
            base0_position_before_variant + 1):
        if column.pos != base1_position_before_variant:
            # if this column isn't centered on the base before the
            # variant then keep going
            continue

        for pileup_element in column.pileups:
            if pileup_element.is_refskip or pileup_element.is_del:
                # if read sequence doesn't actually align to the reference
                # base before a variant, skip it
                continue

            read = pileup_element.alignment

            logging.debug(read)

            # For future reference,  may get overlapping reads
            # which can be identified by having the same name
            name = read.query_name

            if name is None:
                logging.warn("Read at locus %s %d-%d missing name" % (
                    chromosome,
                    base1_position_before_variant,
                    base1_position_after_variant))
                continue

            if read.is_unmapped:
                logging.warn(
                    "How did we get unmapped read '%s' in a pileup?" % (name,))
                continue

            if read.is_secondary and not use_secondary_alignments:
                logging.debug("Skipping secondary alignment of read '%s'")
                continue

            if read.is_duplicate and not use_duplicate_reads:
                logging.debug("Skipping duplicate read '%s'" % name)
                continue

            mapping_quality = read.mapping_quality

            if mapping_quality is None or mapping_quality == 255:
                logging.debug("Skipping read '%s' due to missing MAPQ" % (
                    name,))
                continue
            elif mapping_quality < min_mapping_quality:
                logging.debug("Skipping read '%s' due to low MAPQ: %d < %d" % (
                    read.mapping_quality, min_mapping_quality))
                continue

            sequence = read.query_sequence

            if sequence is None:
                logging.warn("Read '%s' missing sequence")
                continue

            base_qualities = read.query_qualities

            if base_qualities is None:
                logging.warn("Read '%s' missing base qualities" % (name,))
                continue

            #
            # Documentation for pysam.AlignedSegment.get_reference_positions:
            # ------------------------------------------------------------------
            # By default, this method only returns positions in the reference
            # that are within the alignment. If full_length is set, None values
            # will be included for any soft-clipped or unaligned positions
            # within the read. The returned list will thus be of the same length
            # as the read.
            #
            # Source:
            # http://pysam.readthedocs.org/en/latest/
            # api.html#pysam.AlignedSegment.get_reference_positions
            #
            # We want a None value for every read position that does not have a
            # corresponding reference position.
            reference_positions = read.get_reference_positions(
                full_length=True)

            # pysam uses base-0 positions everywhere except region strings
            # Source:
            # http://pysam.readthedocs.org/en/latest/faq.html#pysam-coordinates-are-wrong
            if base0_position_before_variant not in reference_positions:
                logging.debug(
                    "Skipping read '%s' because first position %d not mapped" % (
                        name,
                        base0_position_before_variant))
                continue
            else:
                base0_read_position_before_variant = reference_positions.index(
                    base0_position_before_variant)

            if base0_position_after_variant not in reference_positions:
                logging.debug(
                    "Skipping read '%s' because last position %d not mapped" % (
                        name,
                        base0_position_after_variant))
                continue
            else:
                base0_read_position_after_variant = reference_positions.index(
                    base0_position_after_variant)
            logging.debug("Using read %s" % read)
            yield ReadAtLocus(
                name=name,
                sequence=sequence,
                reference_positions=reference_positions,
                quality_scores=base_qualities,
                base0_read_position_before_variant=base0_read_position_before_variant,
                base0_read_position_after_variant=base0_read_position_after_variant)

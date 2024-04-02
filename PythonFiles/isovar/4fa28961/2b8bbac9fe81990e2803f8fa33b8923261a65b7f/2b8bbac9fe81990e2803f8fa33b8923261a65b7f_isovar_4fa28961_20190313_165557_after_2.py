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
This module combines variant cDNA sequences collected from a BAM file with
the reading frames of annotated reference transcripts to create candidate
translations.
"""


from __future__ import print_function, division, absolute_import
import math


from .logging import get_logger
from .translation_key import TranslationKey


logger = get_logger(__name__)


class Translation(TranslationKey):
    """
    Translated amino acid sequence of a VariantSequenceInReadingFrame for a
    particular ReferenceContext and VariantSequence.
    """
    __slots__ = [
        "untrimmed_variant_sequence",
        "reference_context",
        "variant_sequence_in_reading_frame"
    ]

    def __init__(
            self,
            amino_acids,
            variant_aa_interval_start,
            variant_aa_interval_end,
            ends_with_stop_codon,
            frameshift,
            untrimmed_variant_sequence,
            reference_context,
            variant_sequence_in_reading_frame):
        # TODO:
        #  get rid of untrimmed_variant_sequence by making
        #  VariantSequenceInReadingFrame keep track of its inputs
        self.amino_acids = amino_acids
        self.variant_aa_interval_start = variant_aa_interval_start
        self.variant_aa_interval_end = variant_aa_interval_end
        self.ends_with_stop_codon = ends_with_stop_codon
        self.frameshift = frameshift
        # this variant sequence might differ from the one
        # in variant_sequence_in_reading_frame due to trimming
        # required to match the reference
        self.untrimmed_variant_sequence = untrimmed_variant_sequence
        self.reference_context = reference_context
        self.variant_sequence_in_reading_frame = variant_sequence_in_reading_frame

    @property
    def reads(self):
        """
        RNA reads which were used to construct the coding sequence
        from which we translated these amino acids.
        """
        return self.untrimmed_variant_sequence.reads

    @property
    def reference_cdna_sequence_before_variant(self):
        return (
            self.
            variant_sequence_in_reading_frame.
            reference_cdna_sequence_before_variant)

    @property
    def number_mismatches(self):
        """Only counting number of mismatches before the variant locus.
        """
        return self.number_mismatches_before_variant

    @property
    def number_mismatches_before_variant(self):
        return self.variant_sequence_in_reading_frame.number_mismatches_before_variant

    @property
    def number_mismatches_after_variant(self):
        return self.variant_sequence_in_reading_frame.number_mismatches_after_variant

    @property
    def cdna_sequence(self):
        return self.variant_sequence_in_reading_frame.cdna_sequence

    @property
    def offset_to_first_complete_codon(self):
        return self.variant_sequence_in_reading_frame.offset_to_first_complete_codon

    @property
    def variant_cdna_interval_start(self):
        return self.variant_sequence_in_reading_frame.variant_cdna_interval_start

    @property
    def variant_cdna_interval_end(self):
        return self.variant_sequence_in_reading_frame.variant_cdna_interval_end

    def as_translation_key(self):
        """
        Project Translation object or any other derived class into just a
        TranslationKey, which has fewer fields and can be used as a
        dictionary key.
        """
        return TranslationKey(**{
            name: getattr(self, name)
            for name in TranslationKey._fields})


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
ProteinSequence is a representation of a translated coding sequence,
associated with its supporting (and non-supporting but overlapping) RNA reads.
"""

from __future__ import print_function, division, absolute_import

from .translation_key import TranslationKey
from .translation import Translation
from .logging import get_logger

logger = get_logger(__name__)


class ProteinSequence(TranslationKey):
    """
    Translated amino acid sequence aggregated across possibly multiple
    VariantSequence and ReferenceContext objects (e.g. imagine two distinct
    sequences which contain synonymous codons).

    This is the final result of the isovar variant->expressed peptide pipeline.
    """
    __slots__ = [
        # list of all the Translation objects which support this distinct
        # amino acid sequence
        "translations",
    ]

    def __init__(
            self,
            amino_acids,
            contains_mutation,
            variant_aa_interval_start,
            variant_aa_interval_end,
            ends_with_stop_codon,
            frameshift,
            translations):
        """
        Parameters
        ----------
        amino_acids : str
            Amino acid sequence

        contains_mutation : bool
            Does the amino acid sequence contain a mutation?

        mutant_interval_start : int
            Start of half-open interval for variant amino acids
            in the translated sequence

        mutant_interval_end : int
            End of half-open interval for variant amino acids
            in the translated sequence

        ends_with_stop_codon : bool
            Did the amino acid sequence end due to a stop codon or did we
            just run out of sequence context around the variant?

        frameshift : bool
            Was the variant a frameshift relative to the reference sequence?

        translations : list of Translation
            Translation objects corresponding to each coding sequence + reading
            frame used to determine this ProteinSequence
        """
        TranslationKey.__init__(
            self=self,
            amino_acids=amino_acids,
            variant_aa_interval_start=variant_aa_interval_start,
            variant_aa_interval_end=variant_aa_interval_end,
            ends_with_stop_codon=ends_with_stop_codon,
            frameshift=frameshift)
        self.translations = translations

    @classmethod
    def from_translations(cls, translations):
        """
        Create ProteinSequence from list of Translation objects.
        Fields inherited from TranslationKey (e.g. frameshift,
        ends_with_stop_codon, &c) are inferred from the translation objects
        which must all have the same values for these fields.

        Parameters
        ----------
        translations : list of Translation
            Equivalent translations which might have different cDNA sequences
            but agree in their amino acid sequences.

        Returns
        -------
        ProteinSequence
        """
        if len(translations) == 0:
            raise ValueError(
                "Cannot create ProteinSequence without at least one Translation")

        # fill in fields inherited from TranslationKey by taking value
        # from first Translation iobject and then check to make sure
        # other translations are consistent with this
        first_translation = translations[0]
        kwargs = {"translations": translations}
        for field_name in TranslationKey.__slots__:
            field_value = getattr(first_translation, field_name)
            kwargs[field_name] = field_value
            # check other translations to make sure they have the same value
            # for this field
            for other_translation in translations[1:]:
                other_translation_field_value = getattr(other_translation, field_name)
                if other_translation_field_value != field_value:
                    raise ValueError(
                        "All translations must have same value %s=%s but got %s" % (
                            field_name,
                            field_value,
                            other_translation_field_value))
        return ProteinSequence(**kwargs)

    def __len__(self):
        return len(self.amino_acids)

    @property
    def supporting_reads(self):
        """
        Reads used to create cDNA coding sequence for any Translation
        associated with this ProteinSequence.

        Returns set of AlleleRead
        """
        read_set = set([])
        for translation in self.translations:
            read_set.update(translation.reads)
        return read_set

    @property
    def read_names_supporting_protein_sequence(self):
        """
        Names of reads used to create cDNA coding sequence for any Translation
        associated with this ProteinSequence.

        Returns set of str
        """
        return {r.name for r in self.supporting_reads}

    @property
    def num_supporting_fragments(self):
        """
        Number of unique read names used to construct the cDNA sequences from
        which this protein sequence was translated.

        Returns int
        """
        return len({r.name for r in self.supporting_reads})

    @property
    def num_supporting_reads(self):
        """
        Number of reads used to construct the cDNA sequences from
        which this protein sequence was translated.

        Returns int
        """
        return len(self.supporting_reads)

    @property
    def num_mismatches_before_variant(self):
        """
        Since a ProteinSequence may arise from multiple equivalent translations,
        take the minimum mismatch score from all the translations.

        Returns int
        """
        return min(t.num_mismatches_before_variant for t in self.translations)

    @property
    def num_mismatches_after_variant(self):
        """
        Since a ProteinSequence may arise from multiple equivalent translations,
        take the minimum mismatch score from all the translations.

        Returns int
        """
        return min(t.num_mismatches_after_variant for t in self.translations)

    @property
    def num_mismatches(self):
        """
        Add up the mismatches before and after the variant across all
        translations used to create this ProteinSequence.

        Returns int
        """
        return self.num_mismatches_before_variant + self.num_mismatches_after_variant

    @property
    def transcripts(self):
        """
        Ensembl transcripts which support the reading frame used by
        Translation objects in this ProteinSequence.

        Returns list of pyensembl.Transcript
        """
        transcript_set = set([])
        for translation in self.translations:
            transcript_set.update(translation.reference_context.transcripts)
        return sorted(transcript_set)

    @property
    def transcript_names(self):
        """
        Ensembl transcript names which support the reading frame used by
        Translation objects used in this ProteinSequence.

        Returns list of str
        """
        return [
            t.name
            for t
            in self.transcripts
        ]

    @property
    def transcript_ids(self):
        """
        Ensembl transcript IDs of all transcripts which support the reading
        frame used by Translation objects associated with this
        ProteinSequence.

        Returns list of str
        """
        return [
            transcript.id
            for transcript in self.transcripts
        ]

    @property
    def genes(self):
        """
        Ensembl genes which support the reading frame used by Translation
        objects associated with this ProteinSequence.

        Returns list of pyensembl.Gene
        """
        transcripts = self.transcripts
        genes = {t.gene for t in transcripts}
        return sorted(genes)

    @property
    def gene_names(self):
        """
        Ensembl genes names which support the reading frame used by
        Translation objects used in this ProteinSequence.

        Returns list of str
        """
        return [
            g.name
            for g
            in self.genes
        ]

    @property
    def gene_name(self):
        """
        Return gene name if only one gene is being used to determine the
        reading from to translate this ProteinSequence, or in the very
        unlikely case that multiple genes are being used, concatenate their
        names with a semi-colon separator.

        Returns str
        """
        return ";".join(self.gene_names)

    @property
    def gene_ids(self):
        """
        Ensembl genes IDs which support the reading frame used by
        Translation objects used in this ProteinSequence.

        Returns list of str
        """
        return [g.id for g in self.genes]

    @property
    def cdna_sequences(self):
        """
        Distinct cDNA sequences used to create this protein sequence.

        Returns set of str
        """
        return {t.cdna_sequence for t in self.translations}

    @property
    def num_cdna_sequences(self):
        """
        Number of distinct cDNA sequences used to translate this protein
        sequence.

        Returns int
        """
        return len(self.cdna_sequences)

    @property
    def mutation_start(self):
        """
        Starting interbase index of mutation in protein sequence

        Differs from variant_aa_interval_start by trimming index to never
        exceed sequence length.

        Returns int
        """
        return min(len(self.amino_acids),  self.variant_aa_interval_start)

    @property
    def mutation_end(self):
        """
        Ending interbase index of mutation in protein sequence

        Differs from variant_aa_interval_end by trimming index to never
        exceed sequence length.

        Returns int
        """
        return min(len(self.amino_acids), self.variant_aa_interval_end)

    @property
    def num_mutant_amino_acids(self):
        return self.mutation_end - self.mutation_start

    def ascending_sort_key(self):
        """
        Sort key function used to sort protein sequences lexicographically by these criteria:
            - number of unique supporting fragments
            - number of unique supporting reads (either 1 or 2 per fragment)
            - minimum mismatch versus a supporting reference transcript before variant
            - minimum mismatch versus a supporting reference transcript after variant
            - all else being equal, prefer longer sequences
        """
        return (
            self.num_supporting_fragments,
            self.num_supporting_reads,
            -self.num_mismatches_before_variant,
            -self.num_mismatches_after_variant,
            len(self.amino_acids),
        )

    def subsequence(self, start_idx, end_idx):
        """
        Create a ProteinSequence object covering a subsequence of this
        object's `amino_acids` string.

        Parameters
        ----------
        start_idx : int or None
            Base 0 (inclusive) start index of subsequence

        end_idx : int or None
            Base 0 (exclusive) end index of subsequence

        Returns
        -------
        ProteinSequence
        """

        return ProteinSequence(
            amino_acids=amino_acids,
            contains_mutation=adjusted_contains_mutation,
            variant_aa_interval_start=adjusted_variant_aa_interval_start,
            variant_aa_interval_end=adjusted_variant_aa_interval_end,
            ends_with_stop_codon=adjusted_ends_with_stop_coding,
            frameshift=adjusted_frameshift,
            translations):
        # half-open interval coordinates for variant amino acids
        # in the translated sequence
        "variant_aa_interval_start",
        "variant_aa_interval_end",
        # did the amino acid sequence end due to a stop codon or did we
        # just run out of sequence context around the variant?
        "ends_with_stop_codon",
        # was the variant a frameshift relative to the reference sequence?
        "frameshift"
    ])

        subsequence_end_offset = subsequence_start_offset + subsequence_length
        amino_acids = self.amino_acids[
                      subsequence_start_offset:subsequence_end_offset]
        mutant_amino_acid_start_offset = max(
            0,
            self.mutant_amino_acid_start_offset - subsequence_start_offset)
        mutant_amino_acid_end_offset = min(
            len(amino_acids),
            max(
                0,
                self.mutant_amino_acid_end_offset - subsequence_start_offset))
        n_supporting_reads = self.n_alt_reads_supporting_protein_sequence
        subsequence_mutant_protein_fragment = MutantProteinFragment(
            variant=self.variant,
            gene_name=self.gene_name,
            amino_acids=amino_acids,
            mutant_amino_acid_start_offset=mutant_amino_acid_start_offset,
            mutant_amino_acid_end_offset=mutant_amino_acid_end_offset,
            n_overlapping_reads=self.n_overlapping_reads,
            n_ref_reads=self.n_ref_reads,
            n_alt_reads=self.n_alt_reads,
            n_alt_reads_supporting_protein_sequence=n_supporting_reads,
            supporting_reference_transcripts=self.supporting_reference_transcripts)
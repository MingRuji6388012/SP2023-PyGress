# Copyright (c) 2019. Mount Sinai School of Medicine
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
IsovarResult is a collection of all information gathered about a variant
and any protein sequences which were successfully translated for it.
"""

from __future__ import print_function, division, absolute_import

from collections import OrderedDict

from cached_property import cached_property

from .common import safediv


class IsovarResult(object):
    """
    This object represents all information gathered about a variant,
    which includes the AlleleReads supporting any allele at this variant's
    locus and any protein sequences generated from an alt-allele cDNA
    assembly.
    """

    def __init__(
            self,
            variant,
            read_evidence,
            predicted_effect,
            sorted_protein_sequences=None,
            filter_values=None):
        self.variant = variant
        self.read_evidence = read_evidence
        self.predicted_effect = predicted_effect

        if sorted_protein_sequences is None:
            sorted_protein_sequences = []

        self.sorted_protein_sequences = sorted_protein_sequences

        if filter_values is None:
            self.filter_values = OrderedDict()
        else:
            self.filter_values = filter_values

    @property
    def fields(self):
        """
        List of field names used to construct an IsovarResult instance.
        """
        return [
            "variant",
            "predicted_effect",
            "read_evidence",
            "sorted_protein_sequences",
            "filter_values"
        ]

    def __str__(self):
        field_strings = ["%s=%s" % (k, v) for (k, v) in self.to_dict()]
        return "%s(%s)" % (
            self.__class__.__name,
            ", ".join(field_strings)
        )

    def __repr__(self):
        return str(self)

    def to_dict(self):
        """
        Dictionary representation of fields used to construct this IsovarResult

        Returns dict
        """
        return OrderedDict([
            (k, getattr(self, k))
            for k in self.fields
        ])

    def clone_with_updates(self, **kwargs):
        """
        Create a copy of this IsovarResult object including any new
        parameters in `kwargs`.

        Returns IsovarResult
        """
        for (k, v) in self.to_dict().items():
            if k not in kwargs:
                kwargs[k] = v
        return IsovarResult(**kwargs)

    def to_record(self):
        """
        Create an OrderedDict of essential information from
        this IsovarResult to be used for building a DataFrame across
        variants.

        Returns OrderedDict
        """
        d = OrderedDict([
            ("variant", self.variant.short_description),
            ("overlapping_gene_names",
                ";".join(self.overlapping_gene_names(only_coding=False))),
            ("overlapping_gene_ids",
                ";".join(self.overlapping_gene_ids(only_coding=False))),
            ("overlapping_coding_gene_names",
             ";".join(self.overlapping_gene_names(only_coding=True))),
            ("overlapping_coding_gene_ids",
             ";".join(self.overlapping_gene_ids(only_coding=True))),

        ])

        # get all quantitative fields from this object
        for key in dir(self):
            if key.startswith("num_") or key.startswith("fraction_") or key.startswith("ratio_"):
                d[key] = getattr(self, key)

        ########################################################################
        # predicted protein changes without looking at RNA reads
        ########################################################################
        effect = self.predicted_effect

        d["predicted_effect"] = effect.short_description
        d["predicted_effect_class"] = effect.__class__.__name__

        # list of field names on varcode effect properties
        effect_properties = [
            "gene_name",
            "gene_id",
            "transcript_id",
            "transcript_name",
            "modifies_protein_sequence",
            "original_protein_sequence",
            "aa_mutation_start_offset",
            "aa_mutation_end_offset",
            "mutant_protein_sequence"
        ]
        for field_name in effect_properties:
            # store effect fields with prefix 'predicted_effect_' and use
            # getattr in case the field is not available for all effects
            d["predicted_effect_%s" % field_name] = getattr(
                effect,
                field_name,
                None)

        ########################################################################
        # get the top protein sequence, if one exists
        ########################################################################
        protein_sequence = self.top_protein_sequence

        # list of names we want to use in the result dictionary,
        # paired with names of fields on ProteinSequence
        protein_sequence_properties = [
            ("protein_sequence", "amino_acids"),
            ("protein_sequence_mutation_start", "variant_aa_interval_start"),
            ("protein_sequence_mutation_end", "variant_aa_interval_stop"),
            ("protein_sequence_ends_with_stop_codon", "ends_with_stop_codon"),
            ("protein_sequence_mismatches", "num_mismatches"),
            ("protein_sequence_mismatches_before_variant", "num_mismatches_before_variant"),
            ("protein_sequence_mismatches_after_variant", "num_mismatches_after_variant"),
            ("protein_sequence_num_supporting_reads", "num_supporting_reads"),
            ("protein_sequence_num_supporting_fragments", "num_supporting_fragments"),
            ("protein_sequence_gene_names", "gene_names"),
            ("protein_sequence_gene_ids", "gene_ids"),
            ("protein_sequence_transcript_names", "transcript_names"),
            ("protein_sequence_transcript_ids", "transcript_ids"),
        ]
        for (name, protein_sequence_field) in protein_sequence_properties:
            value = getattr(protein_sequence, protein_sequence_field, None)
            if isinstance(value, (list, set, tuple)):
                value = ";".join(value)
            d[name] = value
        d["trimmed_predicted_mutant_protein_sequence"] = self.trimmed_varcode_sequence
        d["protein_sequence_matches_predicted_effect"] = self.protein_sequence_matches_predicted_effect

        ########################################################################
        # filters
        ########################################################################
        for filter_name, filter_value in self.filter_values.items():
            d["filter:%s" % filter_name] = filter_value
        d["pass"] = self.passes_all_filters

        return d


    @cached_property
    def passes_all_filters(self):
        """
        Does this IsovarResult have True for all the filter values in
        self.filter_values?
        """
        if len(self.filter_values) == 0:
            return True
        else:
            return all(list(self.filter_values.values()))

    @cached_property
    def top_protein_sequence(self):
        """
        If any protein sequences were assembled for this variant then
        return the best according to coverage, number of mismatches
        relative to the reference, number of reference transcripts
        which match sequence before the variant and protein
        sequence length.

        Returns ProteinSequence or None
        """
        if len(self.sorted_protein_sequences) > 0:
            return self.sorted_protein_sequences[0]
        else:
            return None

    @cached_property
    def trimmed_varcode_sequence(self):
        """
        Trim the predicted mutant protein sequence from Varcode
        to match the length of the protein subsequence assembled from RNA.

        Returns str or None
        """
        p = self.top_protein_sequence
        e = self.predicted_effect
        if e is None or p is None:
            return None
        if e.mutant_protein_sequence is None:
            return None
        n_before = p.variant_aa_interval_start
        n_after = len(p.amino_acids) - p.variant_aa_interval_end
        return e.mutant_protein_sequence[
             e.aa_mutation_start_offset - n_before:
             e.aa_mutation_start_offset + len(e.aa_alt) + n_after]

    @cached_property
    def num_amino_acid_mismatches_from_predicted_effect(self):
        """
        Compute the number of mismatches between the mutant protein sequence
        predicted by Varcode and the best supported sequence translated
        from assembled RNA reads by Isovar. We're not allowing any
        insertions or deletions in the middle of the sequences but do
        allow a shorter sequence to start anywhere within a longer one.

        Returns int
        """
        varcode_sequence = self.trimmed_varcode_sequence
        if varcode_sequence is None:
            return None

        protein_sequence = self.top_protein_sequence
        if protein_sequence is None:
            return None

        n_varcode = len(varcode_sequence)
        n_isovar = len(protein_sequence)
        if n_varcode > n_isovar:
            longer = varcode_sequence
            shorter = protein_sequence
        else:
            longer = protein_sequence
            shorter = varcode_sequence
        length_difference = len(longer) - len(shorter)
        best_alignment_score = len(longer)
        for start_offset in range(length_difference + 1):
            # truncate the longer sequence to be the same length
            # as the shorter one
            truncated = longer[start_offset:start_offset + len(shorter)]
            n_mismatches = sum([a != b for (a, b) in zip(shorter, truncated)])
            alignment_score = length_difference + n_mismatches
            if alignment_score < best_alignment_score:
                best_alignment_score = alignment_score
        return best_alignment_score

    @cached_property
    def protein_sequence_matches_predicted_effect(self):
        """
        Does the top protein sequence translated from RNA reads
        match the predicted protein change determined by Varcode?

        Returns bool
        """
        return self.num_amino_acid_mismatches_from_predicted_effect == 0

    @cached_property
    def num_protein_sequences(self):
        """
        Number of distinct protein sequences which were translated from
        assembled RNA reads.

        Returns int
        """
        return len(self.sorted_protein_sequences)

    def transcripts_from_protein_sequences(self, max_num_protein_sequences=None):
        """
        Ensembl transcript IDs of all transcripts which support the reading
        frame used by protein sequences in this IsovarResult.

        Parameters
        ----------
        max_num_protein_sequences : int or None
            If supplied then only consider the top protein sequences up to
            this number.

        Returns list of pyensembl.Transcript
        """
        transcript_set = set([])
        for p in self.sorted_protein_sequences[:max_num_protein_sequences]:
            transcript_set.update(p.transcripts)
        return sorted(transcript_set)

    def transcript_ids_from_protein_sequences(self, max_num_protein_sequences=None):
        """
        Ensembl transcripts IDs which support the reading frame used by protein
        sequences in this IsovarResult.

        Parameters
        ----------
        max_num_protein_sequences : int or None
            If supplied then only consider the top protein sequences up to
            this number.

        Returns list of str
        """
        return sorted({t.id for t in self.transcripts_from_protein_sequences(
            max_num_protein_sequences=max_num_protein_sequences)})

    @cached_property
    def num_transcripts_from_protein_sequences(self):
        """
        Number of genes used by any translated protein sequence associated
        with this IsovarResult.

        Returns int
        """
        return len(self.transcript_ids_from_protein_sequences(
            max_num_protein_sequences=None))

    @cached_property
    def num_transcripts_from_top_protein_sequence(self):
        """
        Number of genes used by any translated protein sequence associated
        with this IsovarResult.

        Returns int
        """
        return len(self.transcript_ids_from_protein_sequences(
            max_num_protein_sequences=1))

    def genes_from_protein_sequences(self, max_num_protein_sequences=None):
        """
        Ensembl genes which support the reading frame used by protein
        sequences in this IsovarResult.

        Parameters
        ----------
        max_num_protein_sequences : int or None
            If supplied then only consider the top protein sequences up to
            this number.

        Returns list of pyensembl.Gene
        """
        transcripts = self.transcripts_from_protein_sequences(
            max_num_protein_sequences=max_num_protein_sequences)
        genes = [t.gene for t in transcripts]
        return sorted(genes)

    def gene_ids_from_protein_sequences(self, max_num_protein_sequences=None):
        """
        Ensembl genes IDs which support the reading frame used by protein
        sequences in this IsovarResult.

        Parameters
        ----------
        max_num_protein_sequences : int or None
            If supplied then only consider the top protein sequences up to
            this number.

        Returns list of str
        """
        return sorted({
            g.id
            for g
            in
            self.genes_from_protein_sequences(
                max_num_protein_sequences=max_num_protein_sequences)
        })

    @cached_property
    def num_genes_from_protein_sequences(self):
        """
        Number of genes used by any translated protein sequence associated
        with this IsovarResult.

        Returns int
        """
        return len(self.gene_ids_from_protein_sequences(
            max_num_protein_sequences=None))

    @cached_property
    def num_genes_from_top_protein_sequence(self):
        """
        Number of genes used by any translated protein sequence associated
        with this IsovarResult.

        Returns int
        """
        return len(self.gene_ids_from_protein_sequences(
            max_num_protein_sequences=1))

    def overlapping_transcripts(self, only_coding=True):
        """
        Transcripts which this variant overlaps.

        Parameters
        ----------
        only_coding : bool
            Only return transcripts which are annotated as coding for a
            protein (default=True)

        Returns set of pyensembl.Transcript objects
        """
        return {
            t
            for t in self.variant.transcripts
            if not only_coding or t.is_protein_coding
        }

    def overlapping_transcript_ids(self, only_coding=True):
        """
        Transcript IDs which this variant overlaps.

        Parameters
        ----------
        only_coding : bool
            Only return transcripts which are annotated as coding for a
            protein (default=True)
        Returns set of str
        """
        return {
            t.id
            for t in self.variant.transcripts
            if not only_coding or t.is_protein_coding
        }

    @cached_property
    def num_overlapping_transcripts(self):
        """
        Number of transcripts overlapped by the variant

        Returns int
        """
        return len(self.overlapping_transcript_ids(only_coding=False))

    @cached_property
    def num_overlapping_coding_transcripts(self):
        """
        Number of coding transcripts overlapped by the variant

        Returns int
        """
        return len(self.overlapping_transcript_ids(only_coding=True))

    def overlapping_genes(self, only_coding=True):
        """
        Genes which this variant overlaps.

        Parameters
        ----------
        only_coding : bool
            Only return genes which are annotated as coding for a
            protein (default=True)

        Returns list of pyensembl.Gene objects
        """
        return sorted({
            g
            for g in self.variant.genes
            if not only_coding or g.is_protein_coding
        })

    def overlapping_gene_names(self, only_coding=True):
        """
        Names of genes which this variant overlaps.

        Parameters
        ----------
        only_coding : bool
           Only return genes which are annotated as coding for a
           protein (default=True)

        Returns list of str
        """
        return [
            g.name for g in self.overlapping_genes(only_coding=only_coding)
        ]

    def overlapping_gene_ids(self, only_coding=True):
        """
        Gene IDs which this variant overlaps.

        Parameters
        ----------
        only_coding : bool
            Only return genes which are annotated as coding for a
            protein (default=True)

        Returns set of str
        """
        return {
            g.id
            for g in self.variant.genes
            if not only_coding or g.is_protein_coding
        }

    @cached_property
    def num_overlapping_genes(self):
        """
        Number of genes overlapped by the variant

        Returns int
        """
        return len(self.overlapping_gene_ids(only_coding=False))

    @cached_property
    def num_overlapping_coding_genes(self):
        """
        Number of coding genes overlapped by the variant

        Returns int
        """
        return len(self.overlapping_gene_ids(only_coding=True))

    @cached_property
    def ref_reads(self):
        """
        AlleleRead objects at this locus which support the reference allele
        """
        return self.read_evidence.ref_reads

    @cached_property
    def alt_reads(self):
        """
        AlleleRead objects at this locus which support the mutant allele
        """
        return self.read_evidence.alt_reads

    @cached_property
    def other_reads(self):
        """
        AlleleRead objects at this locus which support some allele other than
        either the reference or alternate.
        """
        return self.read_evidence.other_reads

    @cached_property
    def ref_read_names(self):
        """
        Names of reference reads at this locus.
        """
        return {r.name for r in self.ref_reads}

    @cached_property
    def alt_read_names(self):
        """
        Names of alt reads at this locus.
        """
        return {r.name for r in self.alt_reads}

    @cached_property
    def ref_and_alt_read_names(self):
        """
        Names of reads which support either the ref or alt alleles.
        """
        return self.ref_read_names.union(self.alt_read_names)

    @cached_property
    def other_read_names(self):
        """
        Names of other (non-alt, non-ref) reads at this locus.
        """
        return {r.name for r in self.other_reads}

    @cached_property
    def all_read_names(self):
        """
        Names of all reads at this locus.
        """
        return self.ref_read_names.union(self.alt_read_names).union(self.other_read_names)

    @cached_property
    def num_total_reads(self):
        """
        Total number of reads at this locus, regardless of allele.
        """
        return self.num_ref_reads + self.num_alt_reads + self.num_other_reads

    @cached_property
    def num_total_fragments(self):
        """
        Total number of distinct fragments at this locus, which also corresponds
        to the total number of read names.
        """
        return len(self.all_read_names)

    @cached_property
    def num_ref_reads(self):
        """
        Number of reads which support the reference allele.
        """
        return len(self.ref_reads)

    @cached_property
    def num_ref_fragments(self):
        """
        Number of distinct fragments which support the reference allele.
        """
        return len(self.ref_read_names)

    @cached_property
    def num_alt_reads(self):
        """
        Number of reads which support the alt allele.
        """
        return len(self.alt_reads)

    @cached_property
    def num_alt_fragments(self):
        """
        Number of distinct fragments which support the alt allele.
        """
        return len(self.alt_read_names)

    @cached_property
    def num_other_reads(self):
        """
        Number of reads which support neither the reference nor alt alleles.
        """
        return len(self.other_reads)

    @cached_property
    def num_other_fragments(self):
        """
        Number of distinct fragments which support neither the reference nor
        alt alleles.
        """
        return len(self.other_read_names)

    @cached_property
    def fraction_ref_reads(self):
        """
        Allelic fraction of the reference allele among all reads at this site.
        """
        return safediv(self.num_ref_reads, self.num_total_reads)

    @cached_property
    def fraction_ref_fragments(self):
        """
        Allelic fraction of the reference allele among all fragments at this site.
        """
        return safediv(self.num_ref_fragments, self.num_total_fragments)

    @cached_property
    def fraction_alt_reads(self):
        """
        Allelic fraction of the variant allele among all reads at this site.
        """
        return safediv(self.num_alt_reads, self.num_total_reads)

    @cached_property
    def fraction_alt_fragments(self):
        """
        Allelic fraction of the variant allele among all fragments at this site.
        """
        return safediv(self.num_alt_fragments, self.num_total_fragments)

    @cached_property
    def fraction_other_reads(self):
        """
        Allelic fraction of the "other" (non-ref, non-alt) alleles among all
        reads at this site.
        """
        return safediv(self.num_other_reads, self.num_total_reads)

    @cached_property
    def fraction_other_fragments(self):
        """
        Allelic fraction of the "other" (non-ref, non-alt) alleles among all
        fragments at this site.
        """
        return safediv(self.num_other_fragments, self.num_total_fragments)

    @cached_property
    def ratio_other_to_ref_reads(self):
        """
        Ratio of the number of reads which support alleles which are neither
        ref/alt to the number of ref reads.
        """
        return safediv(self.num_other_reads, self.num_ref_reads)

    @cached_property
    def ratio_other_to_ref_fragments(self):
        """
        Ratio of the number of fragments which support alleles which are neither
        ref/alt to the number of ref fragments.
        """
        return safediv(self.num_other_fragments, self.num_ref_fragments)

    @cached_property
    def ratio_other_to_alt_reads(self):
        """
        Ratio of the number of reads which support alleles which are neither
        ref/alt to the number of alt reads.
        """
        return safediv(self.num_other_reads, self.num_alt_reads)

    @cached_property
    def ratio_other_to_alt_fragments(self):
        """
        Ratio of the number of fragments which support alleles which are neither
        ref/alt to the number of alt fragments.
        """
        return safediv(self.num_other_fragments, self.num_alt_fragments)

    @cached_property
    def ratio_ref_to_other_reads(self):
        """
        Ratio of the number of reference reads to non-ref/non-alt reads
        """
        return safediv(self.num_ref_reads, self.num_other_reads)

    @cached_property
    def ratio_ref_to_other_fragments(self):
        """
        Ratio of the number of reference fragments to non-ref/non-alt fragments
        """
        return safediv(self.num_ref_fragments, self.num_other_fragments)

    @cached_property
    def ratio_alt_to_other_reads(self):
        """
        Ratio of alt allele reads to non-ref/non-alt reads
        """
        return safediv(self.num_alt_reads, self.num_other_reads)

    @cached_property
    def ratio_alt_to_other_fragments(self):
        """
        Ratio of the number of fragments which support the alt allele
        to the number of non-alt/non-ref allele fragments.
        """
        return safediv(self.num_alt_fragments, self.num_other_fragments)


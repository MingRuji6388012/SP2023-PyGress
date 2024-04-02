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

from collections import namedtuple, defaultdict, OrderedDict

from skbio import DNA
import pandas as pd
from varcode import EffectCollection

from .variant_sequences import variant_sequences_generator
from .logging import create_logger

logger = create_logger(__name__)

# if multiple distinct RNA sequence contexts and/or reference transcripts
# give us the same translation then we group them into a single object
# which summarizes the supporting read count and reference transcript ORFs
# for a unique protein sequence
ProteinFragment = namedtuple(
    "ProteinFragment",
    [
        # number of reads supporting any RNA sequence which translates to
        # this protein sequence
        "number_supporting_reads",
        "variant_protein_sequence",
        "reference_transcript_ids",
        "reference_transcript_names",
        "reference_protein_sequences",
        "cdna_sequences_to_read_names",
    ])

MIN_READS_SUPPORTING_RNA_SEQUENCE = 3
MIN_TRANSCRIPT_PREFIX_LENGTH = 15
MAX_TRANSCRIPT_MISMATCHES = 2
PROTEIN_FRAGMENT_LEGNTH = 25
MAX_SEQUENCES_PER_VARIANT = 5


def rna_sequence_key(fragment_info):
    """
    Get the cDNA (prefix, variant, suffix) fields from a
    TranslationFromReferenceORF object.

    Parameters
    ----------
    fragment_info : TranslationFromReferenceORF

    Returns (str, str, str)
    """
    return (
        fragment_info.cdna_prefix,
        fragment_info.cdna_variant,
        fragment_info.cdna_suffix
    )

def group_protein_fragments(
        protein_fragment_and_read_names_list,
        protein_fragment_length=PROTEIN_FRAGMENT_LEGNTH):
    """
    If we end up with multiple equivalent protein fragments from distinct
    cDNA sequences then we want to group them since ultimately it's
    not relevant which codon gives us a particular amino acid.

    Parameters
    ----------
    fragments_and_read_names : list
        List of tuples containing (1) a TranslationFromReferenceORF object and
        (2) a set of read names from spanning RNA reads for that
        unique sequence.

    protein_fragment_length : int
        Length of the translated protein sequences

    Returns list of ProteinFragment objects.
    """
    # map every distinct protein sequence to a tuple with the following fields:
    # - transcript ID
    # - transcript name
    # - cDNA sequence
    # - reading frame

    protein_sequence_dict = defaultdict(list)
    cdna_to_read_names = {}
    for (translation_info, read_names) in protein_fragment_and_read_names_list:
        cnda_tuple = rna_sequence_key(translation_info)
        if cnda_tuple in cdna_to_read_names:
            assert cdna_to_read_names[cnda_tuple] == read_names
        else:
            cdna_to_read_names[cnda_tuple] = read_names

        protein_sequence = translation_info.variant_protein_sequence
        # if we can chop up the translated protein fragment into shorter pieces
        # then go for it!

        variant_protein_sequence = translation_info.variant_protein_sequence
        ref_protein_sequence = translation_info.reference_protein_sequence
        n_amino_acids = len(variant_protein_sequence)

        for start, end in enumerate(range(protein_fragment_length, n_amino_acids)):

            # all protein fragments must overlap the variant
            if start > translation_info.base0_variant_amino_acid_start_offset:
                break

            if end < translation_info.base0_variant_amino_acid_end_offset:
                continue

            variant_protein_subsequence = protein_sequence[start:end]
            ref_protein_subsequence = ref_protein_sequence[start:end]
            info_tuple = (
                variant_protein_subsequence,
                ref_protein_subsequence,
                translation_info.transcript_id,
                translation_info.transcript_name,
                translation_info.base0_variant_amino_acid_start_offset,
                translation_info.base0_variant_amino_acid_end_offset,
            )
            protein_sequence_dict[protein_sequence].append(info_tuple)

    results = []
    for (protein_sequence, info_objs) in protein_sequence_dict.items():
        transcript_names = list(set([x.transcript_name for x in info_objs]))
        transcript_ids = list(set([x.transcript_id for x in info_objs]))
        cdna_sequence_keys = list(set([rna_sequence_key(x) for x in info_objs]))

        reference_protein_sequences = []

        total_read_count = sum(
            len(cdna_to_read_names[cnda_tuple])
            for cnda_tuple in cdna_sequence_keys)
        transcript_ids = list(set([x.transcript_id for x in info_objs]))
        transcript_names = list(set([x.transcript_name for x in info_objs]))
        reference_protein_sequences = list(set([
            x.reference_protein_sequence
            for x in info_objs]))
        cdna_sequences_to_read_names = {
            rna_sequence_key(x): cdna_to_read_names[rna_sequence_key(x)]
            for x in info_objs
        }
        list(set(
            [rna_sequence_key(x) for x in info_objs]))
        results.append(
            ProteinFragment(
                number_supporting_reads=total_read_count,
                variant_protein_sequence=protein_sequence,
                reference_transcript_ids=transcript_ids,
                reference_transcript_names=transcript_names,
                reference_protein_sequences=reference_protein_sequences,
                cdna_sequences_to_read_names=cdna_sequences_to_read_names))
    return results




def translate_variant(
        variant,
        sequence_context_to_read_names_dict,
        variant_nucleotides,
        reference_transcripts,
        protein_fragment_length=PROTEIN_FRAGMENT_LEGNTH,
        min_reads_supporting_rna_sequence=MIN_READS_SUPPORTING_RNA_SEQUENCE,
        min_transcript_prefix_length=MIN_TRANSCRIPT_PREFIX_LENGTH,
        max_transcript_mismatches=MAX_TRANSCRIPT_MISMATCHES,
        max_sequences=MAX_SEQUENCES_PER_VARIANT):
    """
    Generate possible protein sequences around a variant from surrounding
    context sequences and a set of reference transcripts from the same locus
    which can be used to establish an ORF.

    Parameters
    ----------
    variant : varcode.Variant

    sequence_context_to_read_names_dict : dict
        Dictionary mapping pair of (prefix, suffix) sequences to a set of
        read names which support this sequence.

    variant_nucleotides : str
        Nucleotides found between the (prefix, suffix) pair of each context.

    reference_transcripts : list of pyensembl.Transcript
        Transcripts which are used to establish the reading frame for
        the discovered cDNA sequences.

    protein_fragment_length : int

    min_reads_supporting_rna_sequence : int

    min_transcript_prefix_length : int

    max_transcript_mismatches : int

    max_sequences : int

    chromosome_name : str, optional
        If given, then use this name instead of the chromosome name on
        the variant object (necessary when the BAM's reference is hg19)

    Returns list of tuples containing:
        1) ProteinFragment object
        2) set of read names supporting the protein fragment
    """
    protein_fragments_and_read_names = []

    for i, ((prefix, suffix), read_names) in enumerate(sorted(
            sequence_context_to_read_names_dict.items(),
            key=lambda x: -len(x[1]))):
        logger.info("%d %s|%s %s" % (
            i,
            prefix,
            suffix,
            read_names))

        if i >= max_sequences:
            logger.info(
                "Skipping sequence %s for variant %s, already reached max_sequences (%d)",
                prefix + "|" + suffix,
                variant,
                max_sequences)
            break

        num_reads_supporting_current_sequence = len(read_names)

        if num_reads_supporting_current_sequence < min_reads_supporting_rna_sequence:
            logger.info(
                "Skipping sequence %s for variant %s, too few supporting reads (%d)",
                prefix + "|" + suffix,
                variant,
                num_reads_supporting_current_sequence)
            # we can break here instead of `continue` since the loop iterations
            # are sorted in decreasing order by the number of reads
            break

        for protein_fragment in translate_compatible_reading_frames(
                dna_sequence_prefix=prefix,
                dna_sequence_variant=variant_nucleotides,
                dna_sequence_suffix=suffix,
                base1_variant_start_location=variant.start,
                base1_variant_end_location=variant.end,
                variant_is_insertion=variant.is_insertion,
                variant_is_deletion=variant.is_deletion,
                variant_is_frameshift=not variant.preserves_reading_frame,
                transcripts=reference_transcripts,
                max_transcript_mismatches=max_transcript_mismatches,
                min_transcript_prefix_length=max_transcript_mismatches):
            protein_fragments_and_read_names.append(
                (protein_fragment, read_names))

    logger.info("Gathered protein fragments for %s: %s" % (
        variant,
        protein_fragments_and_read_names))

    grouped_results = group_protein_fragments(
        protein_fragments_and_read_names,
        protein_fragment_length=protein_fragment_length)

    logger.info("Grouped protein fragments for %s: %s" % (
        variant,
        grouped_results))
    return grouped_results


def translate_variants(
        variants,
        samfile,
        transcript_id_whitelist=None,
        protein_fragment_length=PROTEIN_FRAGMENT_LEGNTH,
        min_reads_supporting_rna_sequence=MIN_READS_SUPPORTING_RNA_SEQUENCE,
        min_transcript_prefix_length=MIN_TRANSCRIPT_PREFIX_LENGTH,
        max_transcript_mismatches=MAX_TRANSCRIPT_MISMATCHES,
        max_sequences_per_variant=MAX_SEQUENCES_PER_VARIANT):
    """
    Translates each coding variant in a collection to one or more protein
    fragment sequences (if the variant is not filtered and its spanning RNA
    sequences can be given a reading frame).

    Parameters
    ----------
    variants : varcode.VariantCollection

    samfile : pysam.AlignmentFile

    transcript_id_whitelist : set, optional
        If given, expected to be a set of transcript IDs which we should use
        for determining the reading frame around a variant. If omitted, then
        try to use all overlapping reference transcripts.

    protein_fragment_length : int

    min_reads_supporting_rna_sequence : int

    min_transcript_prefix_length : int

    max_transcript_mismatches : int

    max_sequences_per_variant : int

    Returns a dictionary mapping each variant to DataFrame with the following
    fields:
        -
    """

    # adding 2nt to total RNA sequence length  in case we need to clip 1 or 2
    # bases of the sequence to match a reference ORF but still want to end up
    # with the desired number of amino acids
    rna_sequence_length = protein_fragment_length * 3 + 2

    variant_to_protein_fragments = {}

    for variant, variant_sequences in variant_sequences_generator(
            variants=variants,
            samfile=samfile,
            sequence_length=rna_sequence_length,
            min_reads=min_reads_supporting_rna_sequence):
        print(variant)
        print(variant_sequences)
        sequences_to_read_names_dict = variant_sequences.full_read_names
        variant_nucleotides = variant_sequences.variant_nucleotides

        if len(sequences_to_read_names_dict) == 0:
            logger.info("No variant sequences detected in %s for %s" % (
                samfile.filename,
                variant))
            continue

        predicted_effects = predicted_effects_for_variant(
            variant=variant,
            transcript_id_whitelist=transcript_id_whitelist)

        if len(predicted_effects) == 0:
            logger.info(
                "Skipping variant %s, no predicted coding effects" % (variant,))
            continue

        reference_transcripts = [
            effect.transcript
            for effect in predicted_effects
        ]

        variant_to_protein_fragments[variant] = \
            translate_variant(
                variant=variant,
                sequence_context_to_read_names_dict=sequences_to_read_names_dict,
                variant_nucleotides=variant_nucleotides,
                reference_transcripts=reference_transcripts,
                protein_fragment_length=protein_fragment_length,
                min_reads_supporting_rna_sequence=min_reads_supporting_rna_sequence,
                min_transcript_prefix_length=min_transcript_prefix_length,
                max_transcript_mismatches=max_transcript_mismatches)
    return variant_to_protein_fragments

#
# What do we expect from each variant?
# - total_variant_reads
# - rna_sequences:
# -- sequence
# -- number_reads_supporting_sequence
# -- reading_frames:
# --- reading frame
# --- translated protein fragment
# --- transcripts:
# ---- transcript_id
# ---- transcript_name
# ---- predicted effect prediction
# ---- sequence_prefix
# ---- sequence_ref
# ---- sequence_suffix
# ---- reference protein sequence
# ---- predicted mutant protein sequence

def translate_variants_dataframe(
        variants,
        samfile,
        transcript_id_whitelist=None,
        protein_fragment_length=PROTEIN_FRAGMENT_LEGNTH,
        min_reads_supporting_rna_sequence=MIN_READS_SUPPORTING_RNA_SEQUENCE,
        min_transcript_prefix_length=MIN_TRANSCRIPT_PREFIX_LENGTH,
        max_transcript_mismatches=MAX_TRANSCRIPT_MISMATCHES,
        max_sequences_per_variant=MAX_SEQUENCES_PER_VARIANT):
    """
    Given a collection of variants and a SAM/BAM file of overlapping reads,
    returns a DataFrame of translated protein fragments with the following
    columns:
        chr : str
            Chromosome of variant

        base1_pos : int
            First reference nucleotide affected by variant (or position before
            insertion)

        ref : str
            Reference nucleotides

        alt : str
            Variant nucleotides

        cdna_sequence : str
            cDNA sequence context detected from RNAseq BAM

        cdna_mutation_start_offset : int
            Interbase start offset for variant nucleotides in the cDNA sequence

        cdna_mutation_end_offset : int
            Interbase end offset for variant nucleotides in the cDNA sequence

        supporting_read_count : int
            How many reads fully spanned the cDNA sequence

        variant_protein_sequence : str
            Translated variant protein fragment sequence

        variant_protein_sequence_length : int
            Number of amino acids in each sequence

        reference_transcript_ids : str list

        reference_transcript_names : str list

        reference_protein_sequences : str list

        cdna_sequence_to_support_reads : dict
            Maps distinct (prefix, variant, suffix) triplets to
            names of reads supporting these cDNA sequences

        total_supporting_read_count : int

        """
    # construct a dictionary incrementally which we'll turn into a
    # DataFrame
    column_dict = OrderedDict([
        # fields related to variant
        ("chr", []),
        ("base1_pos", []),
        ("ref", []),
        ("alt", []),
        # fields related to cDNA sequence context around variant
        ("cdna_sequence", []),
        ("supporting_read_count", [])
        ("cdna_mutation_offset_start", []),
        ("cdna_mutation_offset_end", []),
        # fields related to reference transcript from which we're trying to
        # determine a reading frame
        ("reference_transcript_id", []),
        ("reference_transcript_name", []),
        ("reference_cdna_sequence", []),
        ("reference_protein_sequence", []),
        # fields related to translation of variant cDNA from reading frame
        # of the associated transcrpt_id
        ("reading_frame", []),
        ("number_prefix_mismatches", []),
        ("variant_protein_sequence", []),
    ])

    for (variant, transcript_translation_dict) in translate_variants(
            variants,
            samfile,
            transcript_id_whitelist=transcript_id_whitelist,
            protein_fragment_length=protein_fragment_length,
            min_reads_supporting_rna_sequence=min_reads_supporting_rna_sequence,
            min_transcript_prefix_length=min_transcript_prefix_length,
            max_transcript_mismatches=max_transcript_mismatches,
            max_sequences_per_variant=max_sequences_per_variant).items():
        for transcript_id, translation_info in transcript_translation_dict.items():
            # variant info
            column_dict["chr"].append(variant.contig)
            column_dict["base1_pos"].append(variant.start)
            column_dict["ref"].append(variant.ref)
            column_dict["alt"].append(variant.alt)
    df = pd.DataFrame(column_dict)
    return df
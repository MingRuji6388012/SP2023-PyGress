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

import logging
from collections import namedtuple, defaultdict, OrderedDict

from skbio import DNA
import pandas as pd
from varcode import EffectCollection

from .variant_sequences import variant_sequences_generator

# information related to the translation of a RNA sequence context
# in a reading frame determined by a particular reference transcript
TranslationFromReferenceORF = namedtuple(
    "TranslationFromReferenceORF",
    [
        "cdna_prefix",
        "cdna_variant",
        "cdna_suffix",
        "transcript_id",
        "transcript_name",
        "number_transcript_sequence_mismatches",
        "fraction_transcript_sequence_mismatches",
        "reading_frame_at_start_of_cdna_sequence",
        "transcript_sequence_before_variant",
        "variant_protein_sequence",
        "reference_protein_sequence",
        "fragment_aa_start_offset_in_protein",
        "fragment_aa_end_offset_in_protein"
        "variant_aa_start_offset_in_fragment",
        "variant_aa_end_offset_in_fragment",
    ])

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

def translate_compatible_reading_frames(
        dna_sequence_prefix,
        dna_sequence_variant,
        dna_sequence_suffix,
        variant_is_insertion,
        variant_is_deletion,
        variant_is_frameshift,
        base1_variant_start_location,
        base1_variant_end_location,
        transcripts,
        max_transcript_mismatches=MAX_TRANSCRIPT_MISMATCHES,
        min_transcript_prefix_length=MIN_TRANSCRIPT_PREFIX_LENGTH):
    """
    Use the given reference transcripts to attempt to establish the ORF
    of a sequence context extract from RNA reads. It's expected that the
    sequence has been aligned to the reference genome potentially using its
    reverse-complement, and thus the sequence we are given is always from the
    positive strand of DNA.

    Parameters
    ----------
    dna_sequence_prefix : str
        Nucleotides before the variant.

    dna_sequence_variant : str
        Mutated nucleotides, should be empty for a deletion.

    dna_sequence_suffix : str
        Nucleotides after the variant

    variant_is_insertion : bool

    base1_variant_start_location : int
        For deletions and substitutions, this position is the first modified
        nucleotide. For insertions, this is the position before any inserted
        nucleotides.

    base1_variant_end_location : int
        For deletions and substitutions, this is the positions of the last
        affected reference nucleotide. For insertions, this is the location of
        the base after the insertion.

    transcripts : list of pyensembl.Transcript
        List of candidate reference transcripts from which we try to determine
        the ORF of a variant RNA sequence.

    max_transcript_mismatches : int
        Ignore transcripts with more than this number of mismatching nucleotides

    min_transcript_prefix_length : int
        Don't consider transcripts with less than this number of nucleotides
        before the variant position (setting this value to 0 will enable use
        of transcripts without 5' UTR)

    Returns list of TranslationFromReferenceORF objects.
    """
    results = []

    for transcript in transcripts:
        if transcript.strand == "+":
            cdna_prefix = dna_sequence_prefix
            cdna_suffix = dna_sequence_suffix
            cdna_variant = dna_sequence_variant
            variant_in_transcript_idx = transcript.spliced_offset(
                base1_variant_start_location)
        else:
            # if the transcript is on the reverse strand then we have to
            # take the sequence PREFIX|VARIANT|SUFFIX
            # and take the complement of XIFFUS|TNAIRAV|XIFERP
            cdna_prefix = str(DNA(dna_sequence_suffix).reverse_complement())
            cdna_suffix = str(DNA(dna_sequence_prefix).reverse_complement())
            cdna_variant = str(
                DNA(dna_sequence_variant).reverse_complement())
            variant_in_transcript_idx = transcript.spliced_offset(
                base1_variant_end_location)

        if variant_is_insertion:
            # insertions don't actually affect the base referred to
            # by the start position of the variant, but rather the
            # variant gets inserted *after* that position
            query_sequence_end_idx = variant_in_transcript_idx + 1
        else:
            query_sequence_end_idx = variant_in_transcript_idx

        start_codon_idx = min(transcript.start_codon_spliced_offsets)

        if variant_in_transcript_idx < start_codon_idx + 3:
            logging.info(
                "Skipping %s because variant appears in 5' UTR" % (
                    transcript))
            continue

        query_sequence_start_idx = query_sequence_end_idx - len(cdna_prefix)

        if query_sequence_start_idx < 0:
            logging.warn("Transcript %s not long enough for observed sequence" % (
                transcript))
            continue

        transcript_sequence_before_variant = transcript.sequence[
            query_sequence_start_idx:query_sequence_end_idx]

        assert len(transcript_sequence_before_variant) == len(cdna_prefix)
        if len(transcript_sequence_before_variant) < min_transcript_prefix_length:
            continue

        n_mismatch_before = sum(
            xi != yi
            for (xi, yi) in zip(
                transcript_sequence_before_variant, cdna_prefix))

        if n_mismatch > max_transcript_mismatches:
            logging.info(
                "Skipping transcript %s, too many mismatching bases (%d)",
                transcript,
                n_mismatch)
            continue

        # past this point we're assuming that the sequence of the reference
        # transcript up to the variant largely matches the sequence we
        # detected from RNA

        fraction_mismatch = float(n_mismatch) / len(cdna_prefix)

        reading_frame = (query_sequence_start_idx - start_codon_idx) % 3

        if reading_frame == 1:
            # if we're 1 nucleotide into the codon then we need to shift
            # over two more to restore the ORF
            orf_offset = 2
        elif reading_frame == 2:
            orf_offset = 1
        else:
            orf_offset = 0

        logging.info("ORF offset into sequence %s_%s_%s from transcript %s: %d" % (
            cdna_prefix,
            cdna_variant,
            cdna_suffix,
            transcript,
            orf_offset))

        # translate the variant cDNA sequence we detected from spanning reads
        # using the ORF offset from the current reference transcript
        combined_variant_cdna_sequence = DNA(
            cdna_prefix + cdna_variant + cdna_suffix)

        variant_protein_fragment_sequence = str(
            combined_variant_cdna_sequence[orf_offset:].translate())

        logging.info("Combined variant cDNA sequence %s translates to protein %s" % (
            combined_variant_cdna_sequence,
            variant_protein_fragment_sequence))

        # translate the reference sequence using the given ORF offset,
        # we can probably sanity check this by making sure it matches a
        # substring of the transcript.protein_sequence field
        combined_transcript_sequence = DNA(
            transcript.sequence[
                query_sequence_start_idx:
                query_sequence_start_idx + len(combined_variant_cdna_sequence)])

        transcript_protein_fragment_sequence = str(
            combined_transcript_sequence[orf_offset].translate())

        fragment_aa_start_offset_in_protein = (
            query_sequence_start_idx - start_codon_idx) // 3
        fragment_aa_end_offset_in_protein = (
            query_sequence_end_idx - start_codon_idx) // 3 + 1

        n_prefix_codons = n_prefix_nucleotides // 3

        if variant_is_deletion and variant_is_frameshift:
            # after a deletion that shifts the reading frame,
            # there is a partial codon left, which may be different from
            # the original codon at that location. Additionally,
            # the reading frame for all subsequent codons will be different
            # from the reference
            variant_codons_start_offset_in_fragment = None

        # TODO: change variant_codons_start_offset_in_fragment in the
        # TranslationFromReferenceORF to
        # - variant_amino_acids_start_offset_in_fragment
        # - variant_amino_acids_end_offset_in_fragment
        # which are computed from _codons_ offsets by checking which amino
        # acids differ from the reference sequence(s).
        # If a mutated sequence ends up having no differences then
        # we should skip it as a synonymous mutation.

        # TODO #2:
        # Instead of doing this once per sequence/transcript pair, we
        # should precompute the reference transcript sequences and the
        # ORFs they imply and pass in a list of ReferenceTranscriptContext
        # objects with the following field:
        #   sequence_before_variant_locus : cDNA
        #   reading_frame_at_start_of_sequence : int
        #   transcript_ids : str set
        #   transcript_names : str set
        #   gene : str

        variant_aa_start_offset_in_fragment = 0
        last_variant_codon = 0

        """
        # the number of non-mutated codons in the prefix (before the variant)
        # has to trim the ORF offset and then count up by multiples of 3


        aa_prefix = variant_protein_fragment_sequence[:n_prefix_codons]
        aa_variant = variant_protein_fragment_sequence[
            n_prefix_codons:n_prefix_codons + n_variant_codons]
        aa_suffix = variant_protein_fragment_sequence[
            n_prefix_codons + n_variant_codons:]

        assert aa_prefix + aa_variant + aa_suffix == variant_protein_fragment_sequence
                        aa_prefix=aa_prefix,
                aa_variant=aa_variant,
                aa_suffix=aa_suffix)
        """
        results.append(
            TranslationFromReferenceORF(
                cdna_prefix=cdna_prefix,
                cdna_variant=cdna_variant,
                cdna_suffix=cdna_suffix,
                transcript_id=transcript.id,
                transcript_name=transcript.name,
                number_transcript_sequence_mismatches=n_mismatch,
                fraction_transcript_sequence_mismatches=fraction_mismatch,
                reading_frame_at_start_of_cdna_sequence=reading_frame,
                transcript_sequence_before_variant=transcript_sequence_before_variant,
                variant_protein_sequence=variant_protein_fragment_sequence,
                reference_protein_sequence=transcript_protein_fragment_sequence,
                fragment_aa_start_offset_in_protein=fragment_aa_start_offset_in_protein,
                fragment_aa_end_offset_in_protein=fragment_aa_end_offset_in_protein,
                variant_aa_start_offset_in_fragment=variant_aa_start_offset_in_fragment,
                variant_aa_end_offset_in_fragment=variant_aa_end_offset_in_fragment))
    return results

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


def predicted_effects_for_variant(variant, transcript_id_whitelist=None):
    """
    For a given variant, return the set of predicted mutation effects
    on transcripts where this variant results in a predictable non-synonymous
    change to the protein sequence.

    Parameters
    ----------
    variant : varcode.Variant

    transcript_id_whitelist : set
        Filter effect predictions to only include these transcripts

    Returns a varcode.EffectCollection object
    """

    effects = []
    for transcript in variant.transcripts:
        if not transcript.complete:
            logging.info(
                "Skipping transcript %s for variant %s because it's incomplete" % (
                    transcript,
                    variant))
            continue

        if transcript_id_whitelist and transcript.id not in transcript_id_whitelist:
            logging.info(
                "Skipping transcript %s for variant %s because it's not one of %d allowed" % (
                    transcript,
                    variant,
                    len(transcript_id_whitelist)))
            continue
        effects.append(variant.effect_on_transcript(transcript))

    effects = EffectCollection(effects)

    n_total_effects = len(effects)
    logging.info("Predicted %d effects for variant %s" % (
        n_total_effects,
        variant))

    nonsynonymous_coding_effects = effects.drop_silent_and_noncoding()
    logging.info(
        "Keeping %d/%d non-synonymous coding effects for %s" % (
            len(nonsynonymous_coding_effects),
            n_total_effects,
            variant))

    usable_effects = [
        effect
        for effect in nonsynonymous_coding_effects
        if effect.mutant_protein_sequence is not None
    ]
    logging.info(
        "Keeping %d/%d effects with predictable AA sequences for %s" % (
            len(usable_effects),
            len(nonsynonymous_coding_effects),
            variant))
    return usable_effects


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
        logging.info("%d %s|%s %s" % (
            i,
            prefix,
            suffix,
            read_names))

        if i >= max_sequences:
            logging.info(
                "Skipping sequence %s for variant %s, already reached max_sequences (%d)",
                prefix + "|" + suffix,
                variant,
                max_sequences)
            break

        num_reads_supporting_current_sequence = len(read_names)

        if num_reads_supporting_current_sequence < min_reads_supporting_rna_sequence:
            logging.info(
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

    logging.info("Gathered protein fragments for %s: %s" % (
        variant,
        protein_fragments_and_read_names))

    grouped_results = group_protein_fragments(
        protein_fragments_and_read_names,
        protein_fragment_length=protein_fragment_length)

    logging.info("Grouped protein fragments for %s: %s" % (
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
        sequences_to_read_names_dict = variant_sequences.full_read_names
        variant_nucleotides = variant_sequences.variant_nucleotides

        if len(sequences_to_read_names_dict):
            logging.info("No variant sequences detected in %s for %s" % (
                samfile,
                variant))
            continue

        predicted_effects = predicted_effects_for_variant(
            variant=variant,
            transcript_id_whitelist=transcript_id_whitelist)

        if len(predicted_effects) == 0:
            logging.info(
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
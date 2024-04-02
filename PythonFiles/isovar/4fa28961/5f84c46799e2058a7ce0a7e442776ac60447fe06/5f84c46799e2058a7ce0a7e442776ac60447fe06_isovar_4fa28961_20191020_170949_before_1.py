from __future__ import print_function, division, absolute_import

from nose.tools import eq_
from testing_helpers import load_bam, load_vcf, data_path
from mock_objects import make_dummy_protein_sequence

from varcode import VariantCollection

from isovar.read_collector import ReadCollector
from isovar.cli.protein_sequence_args import (
    protein_sequences_dataframe_from_args,
    make_protein_sequences_arg_parser,
)
from isovar.dataframe_helpers import protein_sequences_generator_to_dataframe
from isovar.main import ProteinSequenceCreator
from isovar.protein_sequence_helpers import sort_protein_sequences




def test_sort_protein_sequences():
    protseq_most_reads = make_dummy_protein_sequence(
        n_supporting_variant_reads=50,
        n_supporting_variant_sequences=1,
        n_supporting_reference_transcripts=2,
        n_total_variant_sequences=3,
        n_total_variant_reads=100,
        n_total_reference_transcripts=2)


    protseq_fewest_reads = make_dummy_protein_sequence(
        n_supporting_variant_reads=10,
        n_supporting_variant_sequences=1,
        n_supporting_reference_transcripts=1,
        n_total_variant_sequences=3,
        n_total_variant_reads=100,
        n_total_reference_transcripts=1)
    unsorted_protein_sequences = [
        protseq_fewest_reads,
        protseq_most_reads,
    ]
    expected_order = [
        protseq_most_reads,
        protseq_fewest_reads,
    ]
    eq_(sort_protein_sequences(unsorted_protein_sequences), expected_order)


def variants_to_protein_sequences_dataframe(
        expressed_vcf="data/b16.f10/b16.expressed.vcf",
        not_expressed_vcf="data/b16.f10/b16.not-expressed.vcf",
        tumor_rna_bam="data/b16.f10/b16.combined.sorted.bam",
        min_mapping_quality=0,
        max_protein_sequences_per_variant=1,
        variant_sequence_assembly=False):
    """
    Helper function to load pair of VCFs and tumor RNA BAM
    and use them to generate a DataFrame of expressed variant protein
    sequences.
    """
    expressed_variants = load_vcf(expressed_vcf)
    not_expressed_variants = load_vcf(not_expressed_vcf)

    combined_variants = VariantCollection(
        list(expressed_variants) + list(not_expressed_variants))
    alignment_file = load_bam(tumor_rna_bam)
    read_collector = ReadCollector(min_mapping_quality=min_mapping_quality)
    read_evidence_gen = read_collector.read_evidence_generator(
        variants=combined_variants,
        alignment_file=alignment_file)

    creator = ProteinSequenceCreator(
        max_protein_sequences_per_variant=max_protein_sequences_per_variant,
        variant_sequence_assembly=variant_sequence_assembly)
    protein_sequences_generator = \
        creator.protein_sequences_from_read_evidence_generator(read_evidence_gen)
    df = protein_sequences_generator_to_dataframe(protein_sequences_generator)
    return df, expressed_variants, combined_variants


def test_variants_to_protein_sequences_dataframe_one_sequence_per_variant_with_assembly():
    df, expressed_variants, combined_variants = \
        variants_to_protein_sequences_dataframe(variant_sequence_assembly=True)
    print(df)
    eq_(len(df),
        len(expressed_variants),
        "Expected %d/%d entries to have RNA support, got %d" % (
            len(expressed_variants),
            len(combined_variants),
            len(df)))


def test_variants_to_protein_sequences_dataframe_one_sequence_per_variant_without_assembly():
    df, expressed_variants, combined_variants = \
        variants_to_protein_sequences_dataframe(variant_sequence_assembly=False)
    print(df)
    eq_(len(df),
        len(expressed_variants),
        "Expected %d/%d entries to have RNA support, got %d" % (
            len(expressed_variants),
            len(combined_variants),
            len(df)))


def test_variants_to_protein_sequences_dataframe_filtered_all_reads_by_mapping_quality():
    # since the B16 BAM has all MAPQ=255 values then all the reads should get dropped
    # if we set the minimum quality to 256
    variants = load_vcf("data/b16.f10/b16.vcf")
    alignment_file = load_bam("data/b16.f10/b16.combined.sorted.bam")
    read_collector = ReadCollector(min_mapping_quality=256)
    read_evidence_gen = read_collector.read_evidence_generator(
        variants=variants,
        alignment_file=alignment_file)

    creator = ProteinSequenceCreator(
        max_protein_sequences_per_variant=1,)
    protein_sequences_generator = creator.protein_sequences_from_read_evidence_generator(
        read_evidence_gen)
    df = protein_sequences_generator_to_dataframe(
        protein_sequences_generator)
    print(df)
    eq_(
        len(df),
        0,
        "Expected 0 entries, got %d: %s" % (len(df), df))


def test_protein_sequence_creator_protein_length():
    variants = load_vcf("data/b16.f10/b16.vcf")
    alignment_file = load_bam("data/b16.f10/b16.combined.sorted.bam")
    read_collector = ReadCollector()

    for desired_length in [21, 15, 10]:
        creator = ProteinSequenceCreator(
            max_protein_sequences_per_variant=1,
            protein_sequence_length=desired_length)
        read_evidence_gen = read_collector.read_evidence_generator(
            variants=variants,
            alignment_file=alignment_file)
        protein_sequences_generator = creator.protein_sequences_from_read_evidence_generator(
           read_evidence_gen)
        df = protein_sequences_generator_to_dataframe(protein_sequences_generator)
        print(df)
        protein_sequences = df["amino_acids"]
        print(protein_sequences)
        protein_sequence_lengths = protein_sequences.str.len()
        assert (protein_sequence_lengths == desired_length).all(), (
            protein_sequence_lengths,)


def test_variants_to_protein_sequences_dataframe_protein_sequence_length():
    expressed_variants = load_vcf("data/b16.f10/b16.expressed.vcf")
    parser = make_protein_sequences_arg_parser()
    parser.print_help()
    for desired_length in range(9, 20, 3):
        args = parser.parse_args([
            "--vcf", data_path("data/b16.f10/b16.vcf"),
            "--bam", data_path("data/b16.f10/b16.combined.sorted.bam"),
            "--max-protein-sequences-per-variant", "1",
            "--protein-sequence-length", str(desired_length),
        ])
        df = protein_sequences_dataframe_from_args(args)
        eq_(
            len(df),
            len(expressed_variants),
            "Expected %d entries for protein_sequence_length=%d, got %d results: %s" % (
                len(expressed_variants),
                desired_length,
                len(df),
                df))
        protein_sequences = df["amino_acids"]
        print(protein_sequences)
        protein_sequence_lengths = protein_sequences.str.len()
        assert (protein_sequence_lengths == desired_length).all(), (
            protein_sequence_lengths,)

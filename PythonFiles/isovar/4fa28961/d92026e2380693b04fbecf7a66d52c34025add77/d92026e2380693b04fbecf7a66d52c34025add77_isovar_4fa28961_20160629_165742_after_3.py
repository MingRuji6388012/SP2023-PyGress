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

from ..default_parameters import (
    MIN_READS_SUPPORTING_VARIANT_CDNA_SEQUENCE,
    VARIANT_CDNA_SEQUENCE_LENGTH,
)
from ..variant_sequences import (
    reads_generator_to_sequences_generator,
    variant_sequences_generator_to_dataframe
)
from .rna_reads import allele_reads_generator_from_args, make_rna_reads_arg_parser

def add_variant_sequence_args(parser, add_sequence_length_arg=True):
    rna_sequence_group = parser.add_argument_group("Consensus cDNA sequence")
    rna_sequence_group.add_argument(
        "--min-reads-supporting-variant-sequence",
        type=int,
        default=MIN_READS_SUPPORTING_VARIANT_CDNA_SEQUENCE,
        help="Minimum number of reads supporting a variant sequence")

    # when cDNA sequence length can be inferred from a protein length then
    # we may want to omit this arg
    if add_sequence_length_arg:
        parser.add_argument(
            "--cdna-sequence-sequence-length",
            default=VARIANT_CDNA_SEQUENCE_LENGTH,
            type=int)
    return parser

def make_variant_sequences_arg_parser(add_sequence_length_arg=True, **kwargs):
    parser = make_rna_reads_arg_parser(**kwargs)
    add_variant_sequence_args(parser)
    return parser

def variant_sequences_generator_from_args(args):
    allele_reads_generator = allele_reads_generator_from_args(args)
    return reads_generator_to_sequences_generator(
        allele_reads_generator,
        min_reads_supporting_cdna_sequence=args.min_reads_supporting_variant_sequence,
        preferred_sequence_length=args.cdna_sequence_sequence_length)

def variant_sequences_dataframe_from_args(args):
    variant_sequences_generator = variant_sequences_generator_from_args(args)
    return variant_sequences_generator_to_dataframe(variant_sequences_generator)

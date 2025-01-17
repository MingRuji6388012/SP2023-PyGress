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
Create parser and run Isovar from parsed args
"""

from __future__ import print_function, division, absolute_import

from varcode.cli import variant_collection_from_args

from ..main import run_isovar

from .protein_sequence_args import (
    make_protein_sequences_arg_parser,
    protein_sequence_creator_from_args
)
from .output_args import add_output_args, write_dataframe
from .filter_args import add_filter_args, filter_threshold_dict_from_args
from .rna_args import read_collector_from_args, alignment_file_from_args

def make_isovar_arg_parser(output_filename="isovar-results.csv"):
    parser = make_protein_sequences_arg_parser()
    add_filter_args(parser)
    if output_filename:
        parser = add_output_args(
            parser,
            filename="isovar-results.csv")
    return parser

def run_isovar_from_parsed_args(args):
    variants = variant_collection_from_args(args)
    read_collector = read_collector_from_args(args)
    alignment_file = alignment_file_from_args(args)
    protein_sequence_creator = protein_sequence_creator_from_args(args)
    filter_thresholds = filter_threshold_dict_from_args(args)
    return run_isovar(
        variants=variants,
        alignment_file=alignment_file,
        read_collector=read_collector,
        protein_sequence_creator=protein_sequence_creator,
        filter_thresholds=filter_thresholds)

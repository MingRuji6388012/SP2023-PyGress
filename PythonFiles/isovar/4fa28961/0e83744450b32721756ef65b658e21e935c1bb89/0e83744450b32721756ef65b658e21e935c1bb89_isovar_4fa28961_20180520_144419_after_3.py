# Copyright (c) 2016-2018. Mount Sinai School of Medicine
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
Translate non-synonymous coding variants into mutant protein sequences using an
RNAseq BAM from the same sample. Combine synonymous translations and assign
a read count to each protein sequence.
"""

from __future__ import print_function, division, absolute_import
import sys


from ..common import get_logger
from .protein_sequence_args import (
    make_protein_sequences_arg_parser,
    protein_sequences_dataframe_from_args
)


logger = get_logger(__name__)

parser = make_protein_sequences_arg_parser()

parser.add_argument(
    "--output",
    default="isovar-translate-variants-results.csv",
    help="Name of CSV file which contains predicted sequences")


def run(args=None):
    if args is None:
        args = sys.argv[1:]
    args = parser.parse_args(args)
    logger.info(args)
    df = protein_sequences_dataframe_from_args(args)
    logger.info(df)
    df.to_csv(args.output)

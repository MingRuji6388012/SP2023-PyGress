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

from nose.tools import eq_
from varcode import Variant
from isovar.variant_sequence import variant_reads_to_sequences
from isovar.variant_read import gather_reads_for_single_variant

from testing_helpers import load_bam

def test_sequence_counts_snv():
    samfile = load_bam("data/cancer-wgs-primary.chr12.bam")
    chromosome = "chr12"
    base1_location = 65857041
    ref = "G"
    alt = "C"
    variant = Variant(chromosome, base1_location, ref, alt)

    variant_reads = gather_reads_for_single_variant(
        samfile=samfile,
        chromosome=chromosome,
        variant=variant)

    variant_sequences = variant_reads_to_sequences(
        variant_reads,
        context_size=45)
    assert len(variant_sequences) > 0
    for variant_sequence in variant_sequences:
        print(variant_sequence)
        eq_(variant_sequence.alt, alt)
        eq_(len(variant_sequence.prefix), 45)
        eq_(len(variant_sequence.suffix), 45)
        eq_(
            variant_sequence.prefix + variant_sequence.alt + variant_sequence.suffix,
            variant_sequence.full_sequence)

if __name__ == "__main__":
    test_sequence_counts_snv()

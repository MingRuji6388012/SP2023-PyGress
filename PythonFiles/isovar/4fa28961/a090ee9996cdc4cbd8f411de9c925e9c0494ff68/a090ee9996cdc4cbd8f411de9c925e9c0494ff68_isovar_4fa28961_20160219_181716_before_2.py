from pysam import AlignmentFile
from isovar import sequence_counts, gather_variant_reads
import skbio

def test_sequence_counts_snv():
    samfile = AlignmentFile("data/cancer-wgs-primary.chr12.bam")
    chromosome = "chr12"
    base1_location = 65857041
    ref = "G"
    alt = "C"

    variant_reads = gather_variant_reads(
        samfile=samfile,
        chromosome=chromosome,
        base1_location=base1_location,
        ref=ref,
        alt=alt)
    result = sequence_counts(variant_reads)
    assert result.variant_nucleotides == alt
    assert len(result.sequence_weights) == 1
    assert len(result.fully_supporting_read_counts) == 1
    assert len(result.partially_supporting_read_counts) == 1
    assert len(result.partially_supporting_read_weights) == 1

    for ((prefix, suffix), weight) in sorted(
            result.sequence_weights.items(),
            key=lambda x: x[1]):
        variant = result.variant_nucleotides
        print("%s|%s|%s: %f" % (
            prefix,
            variant,
            suffix,
            weight))

        # translate in three reading frames:
        seq = "%s%s%s" % (prefix, variant, suffix)
        for offset in range(3):
            dna = skbio.DNA(seq[offset:])
            print("frame=%d: %s" % (offset, dna.translate()))

if __name__ == "__main__":
    test_sequence_counts_snv()
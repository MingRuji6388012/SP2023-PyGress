
from pysam import AlignmentFile
from varcode import load_vcf
from isovar import translate_variants

VCF = "data/CELSR1/vcfs/vcf_1.vcf"

BAM = "data/CELSR1/bams/bam_9.bam"

GENOME = "hg19"


def test_translate_variant_collection():
    variants = load_vcf(VCF, genome=GENOME)
    samfile = AlignmentFile(BAM)
    result = translate_variants(variants, samfile)
    assert len(result) > 0, result

if __name__ == "__main__":
    test_translate_variant_collection()

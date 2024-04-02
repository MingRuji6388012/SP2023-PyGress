from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str
from indra.databases import uniprot_client
from indra.util import unicode_strs

def test_query_protein_exists():
    g = uniprot_client.query_protein('P00533')
    assert(g is not None)

def test_query_protein_nonexist():
    g = uniprot_client.query_protein('XXXX')
    assert(g is None)

def test_query_protein_deprecated():
    g = uniprot_client.query_protein('Q8NHX1')
    assert(g is not None)
    gene_name = uniprot_client.get_gene_name('Q8NHX1')
    assert gene_name == 'MAPK3'
    assert unicode_strs(gene_name)

def test_get_family_members():
    members = uniprot_client.get_family_members('RAF')
    assert('ARAF' in members)
    assert('BRAF' in members)
    assert('RAF1' in members)
    assert unicode_strs(members)

def test_get_gene_name_human():
    gene_name = uniprot_client.get_gene_name('P00533')
    assert(gene_name == 'EGFR')
    assert unicode_strs(gene_name)

def test_get_gene_name_nonhuman():
    gene_name = uniprot_client.get_gene_name('P31938')
    assert(gene_name == 'Map2k1')
    assert unicode_strs(gene_name)

def test_is_human():
    assert(uniprot_client.is_human('P00533'))

def test_not_is_human():
    assert(not uniprot_client.is_human('P31938'))

def test_noentry_is_human():
    assert(not uniprot_client.is_human('XXXX'))

def test_get_sequence():
    seq = uniprot_client.get_sequence('P00533')
    assert(len(seq) > 1000)
    assert unicode_strs(seq)

def test_get_modifications():
    mods = uniprot_client.get_modifications('P27361')
    assert(('Phosphothreonine', 202) in mods)
    assert(('Phosphotyrosine', 204) in mods)
    assert unicode_strs(mods)

def test_verify_location():
    assert(uniprot_client.verify_location('P27361', 'T', 202)) 
    assert(not uniprot_client.verify_location('P27361', 'S', 202))
    assert(not uniprot_client.verify_location('P27361', 'T', -1))
    assert(not uniprot_client.verify_location('P27361', 'T', 10000))

def test_get_mnemonic():
    mnemonic = uniprot_client.get_mnemonic('Q02750')
    assert(mnemonic == 'MP2K1_HUMAN')
    assert unicode_strs(mnemonic)

def test_is_secondary_primary():
    assert(not uniprot_client.is_secondary('Q02750'))

def test_is_secondary_secondary():
    assert(uniprot_client.is_secondary('Q96J62'))

def test_get_primary_id_primary():
    assert(uniprot_client.get_primary_id('Q02750') == 'Q02750')

def test_get_primary_id_secondary_hashuman():
    assert(uniprot_client.get_primary_id('Q96J62') == 'P61978')

def test_get_primary_id_secondary_nohuman():
    assert(uniprot_client.get_primary_id('P31848') in
           ['P0A5M5', 'P9WIU6', 'P9WIU7'])

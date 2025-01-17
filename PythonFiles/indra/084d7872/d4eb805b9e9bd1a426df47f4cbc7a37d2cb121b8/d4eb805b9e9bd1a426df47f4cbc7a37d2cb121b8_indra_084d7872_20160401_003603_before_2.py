import os
from indra.java_vm import autoclass, cast
from indra.biopax import biopax_api
import indra.biopax.processor as bpc
from indra.pysb_assembler import PysbAssembler

model_path = os.path.dirname(os.path.abspath(__file__)) +\
             '/../../data/biopax_test.owl'

bp = biopax_api.process_owl(model_path)
uri_prefix = 'http://purl.org/pc2/7/'

'''
def test_hyphenated_agent_names():
    """This query should contain reactions with agent names RAF1-BRAF,
    which need to be canonicalized to Python-compatible names before
    model assembly."""
    bp.get_phosphorylation()
    pa = PysbAssembler()
    pa.add_statements(bp.statements)
    pa.make_model()
'''

def test_paxtools_autoclass():
    autoclass('org.biopax.paxtools.impl.level3.ProteinImpl')

def test_biopaxpattern_autoclass():
    autoclass('org.biopax.paxtools.pattern.PatternBox')

def test_cpath_autoclass():
    autoclass('cpath.client.CPathClient')

def test_listify():
    assert(bpc.listify(1) == [1])
    assert(bpc.listify([1,2] == [1,2]))
    assert(bpc.listify([1] == [1]))

def test_list_listify():
    assert(bpc.list_listify([1]) == [[1]])
    assert(bpc.list_listify([1,2]) == [[1],[2]])
    assert(bpc.list_listify([1, [1,2]]) == [[1], [1,2]])

def test_get_combinations():
    combs = [c for c in bpc.get_combinations([1, 2])]
    assert(combs == [(1,2)])
    combs = [c for c in bpc.get_combinations([1, [3,4]])]
    assert(combs == [(1,3), (1,4)])

def test_has_members_er():
    bpe = bp.model.getByID(uri_prefix +\
                     'ProteinReference_971cec47bcd850e2b7d602f0416edacf')
    bpe = cast(bpc.bp('ProteinReference'), bpe)
    assert(bpc.has_members(bpe))

    bpe = bp.model.getByID('http://identifiers.org/uniprot/P56159')
    bpe = cast(bpc.bp('ProteinReference'), bpe)
    assert(not bpc.has_members(bpe))

def test_has_members_pe():
    bpe = bp.model.getByID('http://identifiers.org/reactome/REACT_117345.2')
    bpe = cast(bpc.bp('Protein'), bpe)
    assert(bpc.has_members(bpe))

def test_has_members_pe2():
    bpe = bp.model.getByID(uri_prefix + 'Protein_7d526475fd43d0a07ca1a596fe81aae0')
    bpe = cast(bpc.bp('Protein'), bpe)
    assert(not bpc.has_members(bpe))

def test_is_pe():
    bpe = bp.model.getByID('http://identifiers.org/reactome/REACT_117345.2')
    bpe = cast(bpc.bp('Protein'), bpe)
    assert(bpc.is_entity(bpe))

def test_is_pe2():
    bpe = bp.model.getByID(uri_prefix +\
                     'ProteinReference_971cec47bcd850e2b7d602f0416edacf')
    bpe = cast(bpc.bp('ProteinReference'), bpe)
    assert(not bpc.is_entity(bpe))

def test_is_er():
    bpe = bp.model.getByID('http://identifiers.org/reactome/REACT_117345.2')
    bpe = cast(bpc.bp('Protein'), bpe)
    assert(not bpc.is_reference(bpe))

def test_is_er2():
    bpe = bp.model.getByID(uri_prefix +\
                     'ProteinReference_971cec47bcd850e2b7d602f0416edacf')
    bpe = cast(bpc.bp('ProteinReference'), bpe)
    assert(bpc.is_reference(bpe))

def test_is_mod():
    bpe = bp.model.getByID(uri_prefix +\
                    'ModificationFeature_59c99eae672d2a11e971a93c7848d5c6')
    bpe = cast(bpc.bp('ModificationFeature'), bpe)
    assert(bpc.is_modification(bpe))

def test_is_mod2():
    bpe = bp.model.getByID(uri_prefix +\
                    'FragmentFeature_806ae27c773eb2d9138269552899c242')
    bpe = cast(bpc.bp('FragmentFeature'), bpe)
    assert(not bpc.is_modification(bpe))

def test_is_complex():
    bpe = bp.model.getByID('http://identifiers.org/reactome/REACT_24213.2')
    bpe = cast(bpc.bp('Complex'), bpe)
    assert(bpc.is_complex(bpe))

def test_is_complex2():
    bpe = bp.model.getByID('http://identifiers.org/reactome/REACT_117345.2')
    bpe = cast(bpc.bp('Protein'), bpe)
    assert(not bpc.is_complex(bpe))

def test_uniprot_id_pe():
    bpe = bp.model.getByID('http://identifiers.org/reactome/REACT_117886.3')
    bpe = cast(bpc.bp('Protein'), bpe)
    ids = bp._get_uniprot_id(bpe)
    assert(set(['Q15303', 'Q2M1W1', 'Q59EW4']) == set(ids))

def test_uniprot_id_er():
    bpe = bp.model.getByID('http://identifiers.org/uniprot/Q15303')
    bpe = cast(bpc.bp('ProteinReference'), bpe)
    ids = bp._get_uniprot_id(bpe)
    assert(set(['Q15303', 'Q2M1W1', 'Q59EW4']) == set(ids))

def test_get_hgnc_id():
    bpe = bp.model.getByID('http://identifiers.org/uniprot/Q15303')
    bpe = cast(bpc.bp('ProteinReference'), bpe)
    hgnc_id = bp._get_hgnc_id(bpe) 
    assert(hgnc_id == 3432)

def test_get_hgnc_name():
    hgnc_name = bp._get_hgnc_name(3432)
    assert(hgnc_name == 'ERBB4')

def test_get_mod_feature():
    bpe = bp.model.getByID(uri_prefix +\
            'ModificationFeature_bd27a53570fb9a5094bb5929bd973217')
    mf = cast(bpc.bp('ModificationFeature'), bpe)
    mc = bpc.BiopaxProcessor._extract_mod_from_feature(mf)
    assert(mc.mod_type == 'phosphorylation')
    assert(mc.residue == 'threonine')
    assert(mc.position == '274')

def test_get_entity_mods():
    bpe = bp.model.getByID(uri_prefix +\
            'Protein_7aeb1631f64e49491b7a0303aaaec536')
    protein = cast(bpc.bp('Protein'), bpe)
    mods = bpc.BiopaxProcessor._get_entity_mods(protein)
    assert(len(mods) == 5)
    mod_types = set([m.mod_type for m in mods])
    assert(mod_types == set(['phosphorylation']))
    residues = set([m.residue for m in mods])
    assert(residues == set(['tyrosine']))
    mod_pos = set([m.position for m in mods])
    assert(mod_pos == set(['1035', '1056', '1128', '1188', '1242']))

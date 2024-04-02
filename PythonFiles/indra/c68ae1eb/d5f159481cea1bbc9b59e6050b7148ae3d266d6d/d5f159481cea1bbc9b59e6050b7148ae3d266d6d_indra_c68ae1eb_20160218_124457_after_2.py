from indra.statements import *
import pkg_resources
import os
from indra.preassembler.hierarchy_manager import HierarchyManager

# Load the hierarchy manager data
ent_path = os.path.join('preassembler', 'entity_hierarchy.rdf')
ent_file = pkg_resources.resource_filename('indra', ent_path)
eh = HierarchyManager(ent_file)

mod_path = os.path.join('preassembler', 'modification_hierarchy.rdf')
mod_file = pkg_resources.resource_filename('indra', mod_path)
mh = HierarchyManager(mod_file)

# Checking for exact matching (except Evidence) between Agents/stmts ---------


def test_matches():
    ras = Agent('Ras')
    raf = Agent('Raf')
    st1 = Complex([ras, raf])
    st2 = Complex([ras, raf])
    assert(st1.matches(st2))

def test_matches_key():
    ras = Agent('Ras')
    raf = Agent('Raf')
    st1 = Complex([ras, raf])
    st2 = Complex([ras, raf])
    assert(st1.matches_key() == st2.matches_key())

def test_matches2():
    raf = Agent('Raf')
    mek = Agent('Mek')
    st1 = Phosphorylation(raf, mek, 'Phosphorylation', None)
    st2 = Phosphorylation(raf, mek, 'Phosphorylation', None)
    assert(st1.matches(st2))

def test_matches_key2():
    raf = Agent('Raf')
    mek = Agent('Mek')
    st1 = Phosphorylation(raf, mek, 'Phosphorylation', None)
    st2 = Phosphorylation(raf, mek, 'Phosphorylation', None)
    assert(st1.matches_key() == st2.matches_key())

def test_not_matches():
    raf = Agent('Raf')
    mek = Agent('Mek')
    st1 = Phosphorylation(raf, mek, 'Phosphorylation', None)
    st2 = Phosphorylation(raf, mek, 'PhosphorylationTyrosine', None)
    assert(not st1.matches(st2))

def test_not_matches_key():
    raf = Agent('Raf')
    mek = Agent('Mek')
    st1 = Phosphorylation(raf, mek, 'Phosphorylation', None)
    st2 = Phosphorylation(raf, mek, 'PhosphorylationTyrosine', None)
    assert(st1.matches_key() != st2.matches_key())

def test_matches_dbrefs():
    hras1 = Agent('HRAS', db_refs={'hgnc': 1111})
    hras2 = Agent('HRAS', db_refs={'hgnc': 9999})
    assert(hras1.matches(hras2))

def test_matches_key_dbrefs():
    hras1 = Agent('HRAS', db_refs={'hgnc': 1111})
    hras2 = Agent('HRAS', db_refs={'hgnc': 9999})
    assert(hras1.matches_key() == hras2.matches_key())

def test_matches_bound():
    hras1 = Agent('HRAS',
        bound_conditions=[BoundCondition(Agent('BRAF'), True)])
    hras2 = Agent('HRAS',
        bound_conditions=[BoundCondition(Agent('BRAF'), True)])
    assert(hras1.matches(hras2))

def test_matches_key_bound():
    hras1 = Agent('HRAS',
        bound_conditions=[BoundCondition(Agent('BRAF'), True)])
    hras2 = Agent('HRAS',
        bound_conditions=[BoundCondition(Agent('BRAF'), True)])
    assert(hras1.matches_key() == hras2.matches_key())

def test_not_matches_bound():
    hras1 = Agent('HRAS',
        bound_conditions=[BoundCondition(Agent('BRAF'), True)])
    hras2 = Agent('HRAS',
        bound_conditions=[BoundCondition(Agent('RAF1'), True)])
    assert(not hras1.matches(hras2))

def test_not_matches_key_bound():
    hras1 = Agent('HRAS',
        bound_conditions=[BoundCondition(Agent('BRAF'), True)])
    hras2 = Agent('HRAS',
        bound_conditions=[BoundCondition(Agent('RAF1'), True)])
    assert(hras1.matches_key() != hras2.matches_key())

def test_not_matches_bound2():
    hras1 = Agent('HRAS',
        bound_conditions=[BoundCondition(Agent('BRAF'), True)])
    hras2 = Agent('HRAS',
        bound_conditions=[BoundCondition(Agent('BRAF'), False)])
    assert(not hras1.matches(hras2))

def test_not_matches_key_bound2():
    hras1 = Agent('HRAS',
        bound_conditions=[BoundCondition(Agent('BRAF'), True)])
    hras2 = Agent('HRAS',
        bound_conditions=[BoundCondition(Agent('BRAF'), False)])
    assert(hras1.matches_key() != hras2.matches_key())

def test_matches_bound_multiple():
    hras1 = Agent('HRAS', bound_conditions=[BoundCondition(Agent('BRAF'), True),
                                            BoundCondition(Agent('RAF1'), True)])
    hras2 = Agent('HRAS', bound_conditions=[BoundCondition(Agent('BRAF'), True),
                                            BoundCondition(Agent('RAF1'), True)])
    assert(hras1.matches(hras2))

def test_matches_key_bound_multiple():
    hras1 = Agent('HRAS', bound_conditions=[BoundCondition(Agent('BRAF'), True),
                                            BoundCondition(Agent('RAF1'), True)])
    hras2 = Agent('HRAS', bound_conditions=[BoundCondition(Agent('BRAF'), True),
                                            BoundCondition(Agent('RAF1'), True)])
    assert(hras1.matches_key() == hras2.matches_key())

def test_matches_bound_multiple_order():
    hras1 = Agent('HRAS', bound_conditions=[BoundCondition(Agent('RAF1'), True),
                                            BoundCondition(Agent('BRAF'), True)])
    hras2 = Agent('HRAS', bound_conditions=[BoundCondition(Agent('BRAF'), True),
                                            BoundCondition(Agent('RAF1'), True)])
    assert(hras1.matches(hras2))

def test_matches_key_bound_multiple_order():
    hras1 = Agent('HRAS', bound_conditions=[BoundCondition(Agent('RAF1'), True),
                                            BoundCondition(Agent('BRAF'), True)])
    hras2 = Agent('HRAS', bound_conditions=[BoundCondition(Agent('BRAF'), True),
                                            BoundCondition(Agent('RAF1'), True)])
    assert(hras1.matches_key() == hras2.matches_key())

# Check matches implementations for all statement types ---------------------
def test_matches_selfmod():
    """Test matching of entities only, entities match only on name."""
    nras1 = Agent('NRAS', db_refs = {'HGNC': '7989'})
    nras2 = Agent('NRAS', db_refs = {'HGNC': 'dummy'})
    st1 = Autophosphorylation(nras1, 'PhosphorylationTyrosine', '32',
                          evidence=Evidence(text='foo'))
    st2 = Autophosphorylation(nras1, 'PhosphorylationTyrosine', '32',
                          evidence=Evidence(text='bar'))
    st3 = Autophosphorylation(nras2, 'Phosphorylation', None,
                          evidence=Evidence(text='bar'))
    assert(st1.matches(st2))
    assert(not st1.matches(st3))

def test_matches_activityactivity():
    """Test matching of entities only, entities match only on name."""
    src = Agent('SRC', db_refs = {'HGNC': '11283'})
    nras1 = Agent('NRAS', db_refs = {'HGNC': '7989'})
    nras2 = Agent('NRAS', db_refs = {'HGNC': 'dummy'})
    st1 = ActivityActivity(src, 'Kinase1', 'increases1',
                           nras1, 'GtpBoundActivity1',
                           evidence=Evidence(text='foo'))
    st2 = ActivityActivity(src, 'Kinase1', 'increases1',
                           nras1, 'GtpBoundActivity1',
                           evidence=Evidence(text='bar'))
    st3 = ActivityActivity(src, 'Kinase2', 'increases2',
                           nras2, 'GtpBoundActivity2', 
                           evidence=Evidence(text='bar'))
    assert(st1.matches(st2))
    assert(not st1.matches(st3))

def test_matches_activitymod():
    """Test matching of entities only, entities match only on name."""
    nras1 = Agent('NRAS', db_refs = {'HGNC': '7989'})
    nras2 = Agent('NRAS', db_refs = {'HGNC': 'dummy'})
    st1 = ActivityModification(nras1, 'PhosphorylationTyrosine', '32',
                               'increases1', 'GtpBoundActivity1',
                               evidence=Evidence(text='foo'))
    st2 = ActivityModification(nras1, 'PhosphorylationTyrosine', '32',
                               'increases1', 'GtpBoundActivity1',
                               evidence=Evidence(text='bar'))
    st3 = ActivityModification(nras2, 'Phosphorylation', None,
                               'increases2', 'GtpBoundActivity2',
                               evidence=Evidence(text='bar'))
    assert(st1.matches(st2))
    assert(not st1.matches(st3))

def test_matches_activatingsub():
    """Test matching of entities only, entities match only on name."""
    nras1 = Agent('NRAS', db_refs = {'HGNC': '7989'})
    nras2 = Agent('NRAS', db_refs = {'HGNC': 'dummy'})
    st1 = ActivatingSubstitution(nras1, 'G', '12', 'D', 'GtpBoundActivity1',
                                 'increases1', evidence=Evidence(text='foo'))
    st2 = ActivatingSubstitution(nras1, 'G', '12', 'D', 'GtpBoundActivity1',
                                 'increases1', evidence=Evidence(text='bar'))
    st3 = ActivatingSubstitution(nras2, 'Q', '61', 'L', 'GtpBoundActivity2',
                                 'increases2', evidence=Evidence(text='bar'))
    assert(st1.matches(st2))
    assert(not st1.matches(st3))

def test_matches_rasgef():
    """Test matching of entities only, entities match only on name."""
    sos1 = Agent('SOS1', db_refs = {'HGNC': 'sos1'})
    sos2 = Agent('SOS1', db_refs = {'HGNC': 'sos2'})
    nras1 = Agent('NRAS', db_refs = {'HGNC': '7989'})
    nras2 = Agent('NRAS', db_refs = {'HGNC': 'dummy'})
    st1 = RasGef(sos1, 'GtpBoundActivity1', nras1,
                 evidence=Evidence(text='foo'))
    st2 = RasGef(sos1, 'GtpBoundActivity1', nras1,
                 evidence=Evidence(text='bar'))
    st3 = RasGef(sos2, 'GtpBoundActivity2', nras2,
                 evidence=Evidence(text='bar'))
    assert(st1.matches(st2))
    assert(not st1.matches(st3))

def test_matches_rasgap():
    rasa1 = Agent('RASA1', db_refs = {'HGNC': 'rasa1'})
    rasa2 = Agent('RASA1', db_refs = {'HGNC': 'rasa2'})
    nras1 = Agent('NRAS', db_refs = {'HGNC': '7989'})
    nras2 = Agent('NRAS', db_refs = {'HGNC': 'dummy'})
    st1 = RasGap(rasa1, 'GtpBoundActivity1', nras1,
                 evidence=Evidence(text='foo'))
    st2 = RasGap(rasa1, 'GtpBoundActivity1', nras1,
                 evidence=Evidence(text='bar'))
    st3 = RasGap(rasa2, 'GtpBoundActivity2', nras2,
                 evidence=Evidence(text='bar'))
    assert(st1.matches(st2))
    assert(not st1.matches(st3))

def test_matches_complex():
    ksr1 = Agent('KSR1', db_refs = {'HGNC': 'ksr1'})
    ksr2 = Agent('KSR1', db_refs = {'HGNC': 'ksr2'})
    braf1 = Agent('BRAF', db_refs = {'HGNC': 'braf1'})
    braf2 = Agent('BRAF', db_refs = {'HGNC': 'braf2'})
    map2k1 = Agent('MAP2K1', db_refs = {'HGNC': 'map2k1'})
    map2k2 = Agent('MAP2K1', db_refs = {'HGNC': 'map2k2'})
    st1 = Complex([ksr1, braf1, map2k1], evidence=Evidence(text='foo'))
    st2 = Complex([ksr1, braf1, map2k1], evidence=Evidence(text='bar'))
    assert(st1.matches(st2))


# Entity matching between statements ----------------------------------------
def test_agent_entity_match():
    """Agents match only on name."""
    nras1 = Agent('NRAS', db_refs = {'HGNC': '7989'})
    nras2 = Agent('NRAS', db_refs = {'HGNC': 'dummy'})
    assert(nras1.entity_matches(nras2))

def test_entities_match_mod():
    """Test matching of entities only, entities match only on name."""
    src = Agent('SRC', db_refs = {'HGNC': '11283'})
    nras1 = Agent('NRAS', db_refs = {'HGNC': '7989'})
    nras2 = Agent('NRAS', db_refs = {'HGNC': 'dummy'})
    st1 = Phosphorylation(src, nras1, 'PhosphorylationTyrosine', '32',
                          evidence=Evidence(text='foo'))
    st2 = Phosphorylation(src, nras2, 'Phosphorylation', None,
                          evidence=Evidence(text='bar'))
    assert(st1.entities_match(st2))

def test_entities_match_selfmod():
    """Test matching of entities only, entities match only on name."""
    nras1 = Agent('NRAS', db_refs = {'HGNC': '7989'})
    nras2 = Agent('NRAS', db_refs = {'HGNC': 'dummy'})
    st1 = Autophosphorylation(nras1, 'PhosphorylationTyrosine', '32',
                          evidence=Evidence(text='foo'))
    st2 = Autophosphorylation(nras2, 'Phosphorylation', None,
                          evidence=Evidence(text='bar'))
    assert(st1.entities_match(st2))

def test_entities_match_activityactivity():
    """Test matching of entities only, entities match only on name."""
    src = Agent('SRC', db_refs = {'HGNC': '11283'})
    nras1 = Agent('NRAS', db_refs = {'HGNC': '7989'})
    nras2 = Agent('NRAS', db_refs = {'HGNC': 'dummy'})
    st1 = ActivityActivity(src, 'Kinase1', 'increases1',
                           nras1, 'GtpBoundActivity1',
                           evidence=Evidence(text='foo'))
    st2 = ActivityActivity(src, 'Kinase2', 'increases2',
                           nras2, 'GtpBoundActivity2', 
                           evidence=Evidence(text='bar'))
    assert(st1.entities_match(st2))

def test_entities_match_activitymod():
    """Test matching of entities only, entities match only on name."""
    nras1 = Agent('NRAS', db_refs = {'HGNC': '7989'})
    nras2 = Agent('NRAS', db_refs = {'HGNC': 'dummy'})
    st1 = ActivityModification(nras1, 'PhosphorylationTyrosine', '32',
                               'increases1', 'GtpBoundActivity1',
                               evidence=Evidence(text='foo'))
    st2 = ActivityModification(nras2, 'Phosphorylation', None,
                               'increases2', 'GtpBoundActivity2',
                               evidence=Evidence(text='bar'))
    assert(st1.entities_match(st2))

def test_entities_match_activatingsub():
    """Test matching of entities only, entities match only on name."""
    nras1 = Agent('NRAS', db_refs = {'HGNC': '7989'})
    nras2 = Agent('NRAS', db_refs = {'HGNC': 'dummy'})
    st1 = ActivatingSubstitution(nras1, 'G', '12', 'D', 'GtpBoundActivity1',
                                 'increases1', evidence=Evidence(text='foo'))
    st2 = ActivatingSubstitution(nras2, 'Q', '61', 'L', 'GtpBoundActivity2',
                                 'increases2', evidence=Evidence(text='bar'))
    assert(st1.entities_match(st2))

def test_entities_match_rasgef():
    """Test matching of entities only, entities match only on name."""
    sos1 = Agent('SOS1', db_refs = {'HGNC': 'sos1'})
    sos2 = Agent('SOS1', db_refs = {'HGNC': 'sos2'})
    nras1 = Agent('NRAS', db_refs = {'HGNC': '7989'})
    nras2 = Agent('NRAS', db_refs = {'HGNC': 'dummy'})
    st1 = RasGef(sos1, 'GtpBoundActivity1', nras1,
                 evidence=Evidence(text='foo'))
    st2 = RasGef(sos2, 'GtpBoundActivity2', nras2,
                 evidence=Evidence(text='bar'))
    assert(st1.entities_match(st2))

def test_entities_match_rasgap():
    """Test matching of entities only, entities match only on name."""
    rasa1 = Agent('RASA1', db_refs = {'HGNC': 'rasa1'})
    rasa2 = Agent('RASA1', db_refs = {'HGNC': 'rasa2'})
    nras1 = Agent('NRAS', db_refs = {'HGNC': '7989'})
    nras2 = Agent('NRAS', db_refs = {'HGNC': 'dummy'})
    st1 = RasGap(rasa1, 'GtpBoundActivity1', nras1,
                 evidence=Evidence(text='foo'))
    st2 = RasGap(rasa2, 'GtpBoundActivity2', nras2,
                 evidence=Evidence(text='bar'))
    assert(st1.entities_match(st2))

def test_entities_match_complex():
    """Test matching of entities only, entities match only on name."""
    ksr1 = Agent('KSR1', db_refs = {'HGNC': 'ksr1'})
    ksr2 = Agent('KSR1', db_refs = {'HGNC': 'ksr2'})
    braf1 = Agent('BRAF', db_refs = {'HGNC': 'braf1'})
    braf2 = Agent('BRAF', db_refs = {'HGNC': 'braf2'})
    map2k1 = Agent('MAP2K1', db_refs = {'HGNC': 'map2k1'})
    map2k2 = Agent('MAP2K1', db_refs = {'HGNC': 'map2k2'})
    st1 = Complex([ksr1, braf1, map2k1], evidence=Evidence(text='foo'))
    st2 = Complex([ksr2, braf2, map2k2], evidence=Evidence(text='bar'))
    assert(st1.entities_match(st2))

def test_agent_superfamily_refinement():
    """A gene-level statement should be supported by a family-level
    statement."""
    ras = Agent('RAS', db_refs = {'FA': '03663'})
    nras = Agent('NRAS', db_refs = {'HGNC': '7989'})
    assert nras.refinement_of(ras, eh, mh)
    assert not ras.refinement_of(nras, eh, mh)
    # The top-level list should contain only one statement, the gene-level
    # one, supported by the family one.

def test_agent_boundcondition_refinement():
    """A gene-level statement should be supported by a family-level
    statement."""
    bc1 = BoundCondition(Agent('RASA1', db_refs = {'HGNC': 'rasa1'}), True)
    bc2 = BoundCondition(Agent('RASA2', db_refs = {'HGNC': 'rasa2'}), True)
    bc3 = BoundCondition(Agent('RASA2', db_refs = {'HGNC': 'rasa2'}), False)
    nras1 = Agent('NRAS', db_refs = {'HGNC': '7989'}, bound_conditions=[bc1])
    nras2 = Agent('NRAS', db_refs = {'HGNC': '7989'}, bound_conditions=[bc2])
    nras2b = Agent('NRAS', db_refs = {'HGNC': '7989'}, bound_conditions=[bc3])
    nras3 = Agent('NRAS', db_refs = {'HGNC': '7989'})
    assert nras1.refinement_of(nras3, eh, mh)
    assert nras2.refinement_of(nras3, eh, mh)
    # A statement with identical bound conditions counts as a refinement of itself
    # at least for now
    assert nras1.refinement_of(nras1, eh, mh)
    assert nras3.refinement_of(nras3, eh, mh)

    assert not nras1.refinement_of(nras2, eh, mh)
    assert not nras2.refinement_of(nras1, eh, mh)
    assert not nras3.refinement_of(nras1, eh, mh)
    assert not nras3.refinement_of(nras2, eh, mh)
    assert not nras2.refinement_of(nras2b, eh, mh)

def test_agent_modification_refinement():
    """A gene-level statement should be supported by a family-level
    statement."""
    mek1 = Agent('MAP2K1', db_refs = {'HGNC': 'asdf'},
                mods=['Phosphorylation'], mod_sites=[None])
    mek2 = Agent('MAP2K1', db_refs = {'HGNC': 'asdf'},
                mods=['Phosphorylation'], mod_sites=['218'])
    mek3 = Agent('MAP2K1', db_refs = {'HGNC': 'asdf'},
                mods=['Phosphorylation'], mod_sites=['222'])
    mek4 = Agent('MAP2K1', db_refs = {'HGNC': 'asdf'},
                mods=['Phosphorylation', 'Phosphorylation'],
                mod_sites=['218', '222'])
    mek5 = Agent('MAP2K1', db_refs = {'HGNC': 'asdf'},
                mods=['PhosphorylationSerine'], mod_sites=[None])
    mek6 = Agent('MAP2K1', db_refs = {'HGNC': 'asdf'},
                mods=['PhosphorylationSerine'], mod_sites=['218'])
    mek7 = Agent('MAP2K1', db_refs = {'HGNC': 'asdf'},
                mods=['PhosphorylationSerine'], mod_sites=['222'])
    mek8 = Agent('MAP2K1', db_refs = {'HGNC': 'asdf'},
                mods=['PhosphorylationSerine', 'PhosphorylationSerine'],
                mod_sites=['218', '222'])

    # mek1 agent is refined by all others
    assert mek2.refinement_of(mek1, eh, mh)
    assert mek3.refinement_of(mek1, eh, mh)
    assert mek4.refinement_of(mek1, eh, mh)
    assert mek5.refinement_of(mek1, eh, mh)
    assert mek6.refinement_of(mek1, eh, mh)
    assert mek7.refinement_of(mek1, eh, mh)
    assert mek8.refinement_of(mek1, eh, mh)
    # mek2
    assert not mek1.refinement_of(mek2, eh, mh)
    assert not mek3.refinement_of(mek2, eh, mh) # Different site
    assert mek4.refinement_of(mek2, eh, mh)
    assert not mek5.refinement_of(mek2, eh, mh) # Cross-relationship
    assert mek6.refinement_of(mek2, eh, mh)
    assert not mek7.refinement_of(mek2, eh, mh) # Different site
    assert mek8.refinement_of(mek2, eh, mh)
    # mek3
    assert not mek1.refinement_of(mek3, eh, mh)
    assert not mek2.refinement_of(mek3, eh, mh)
    assert mek4.refinement_of(mek3, eh, mh)
    assert not mek5.refinement_of(mek3, eh, mh)
    assert not mek6.refinement_of(mek3, eh, mh)
    assert mek7.refinement_of(mek3, eh, mh)
    assert mek8.refinement_of(mek3, eh, mh)
    # mek4
    assert not mek1.refinement_of(mek4, eh, mh)
    assert not mek2.refinement_of(mek4, eh, mh)
    assert not mek3.refinement_of(mek4, eh, mh)
    assert not mek5.refinement_of(mek4, eh, mh)
    assert not mek6.refinement_of(mek4, eh, mh)
    assert not mek7.refinement_of(mek4, eh, mh)
    assert mek8.refinement_of(mek4, eh, mh)
    # mek5
    assert not mek1.refinement_of(mek5, eh, mh)
    assert not mek2.refinement_of(mek5, eh, mh)
    assert not mek3.refinement_of(mek5, eh, mh)
    assert not mek4.refinement_of(mek5, eh, mh)
    assert mek6.refinement_of(mek5, eh, mh)
    assert mek7.refinement_of(mek5, eh, mh)
    assert mek8.refinement_of(mek5, eh, mh)
    # mek6
    assert not mek1.refinement_of(mek6, eh, mh)
    assert not mek2.refinement_of(mek6, eh, mh)
    assert not mek3.refinement_of(mek6, eh, mh)
    assert not mek4.refinement_of(mek6, eh, mh)
    assert not mek5.refinement_of(mek6, eh, mh)
    assert not mek7.refinement_of(mek6, eh, mh)
    assert mek8.refinement_of(mek6, eh, mh)
    # mek7
    assert not mek1.refinement_of(mek7, eh, mh)
    assert not mek2.refinement_of(mek7, eh, mh)
    assert not mek3.refinement_of(mek7, eh, mh)
    assert not mek4.refinement_of(mek7, eh, mh)
    assert not mek5.refinement_of(mek7, eh, mh)
    assert not mek6.refinement_of(mek7, eh, mh)
    assert mek8.refinement_of(mek7, eh, mh)
    # mek8
    assert not mek1.refinement_of(mek8, eh, mh)
    assert not mek2.refinement_of(mek8, eh, mh)
    assert not mek3.refinement_of(mek8, eh, mh)
    assert not mek4.refinement_of(mek8, eh, mh)
    assert not mek5.refinement_of(mek8, eh, mh)
    assert not mek6.refinement_of(mek8, eh, mh)
    assert not mek7.refinement_of(mek8, eh, mh)


# TODO expand tests to also check for things that should NOT match (different
# agent names)

# TODO Expand match tests to 

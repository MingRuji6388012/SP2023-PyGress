from __future__ import print_function, unicode_literals
import sys
from os.path import dirname, join
import indra.statements as ist
from indra import trips
from indra.assemblers import PysbAssembler

test_small_file = join(dirname(__file__), 'test_small.xml')

def test_phosphorylation():
    tp = trips.process_text('BRAF phosphorylates MEK1 at Ser222.')
    assert(len(tp.statements) == 1)
    st = tp.statements[0]
    assert(isinstance(st, ist.Phosphorylation))
    assert(st.residue == 'S')
    assert(st.position == '222')

def test_phosphorylation_noresidue():
    tp = trips.process_text('BRAF phosphorylates MEK1.')
    assert(len(tp.statements) == 1)
    st = tp.statements[0]
    assert(isinstance(st, ist.Phosphorylation))
    assert(st.residue is None)
    assert(st.position is None)

def test_phosphorylation_nosite():
    tp = trips.process_text('BRAF phosphorylates MEK1 at Serine.')
    assert(len(tp.statements) == 1)
    st = tp.statements[0]
    assert(isinstance(st, ist.Phosphorylation))
    assert(st.residue == 'S')
    assert(st.position is None)

def test_actmod():
    tp = trips.process_text('MEK1 phosphorylated at Ser222 is activated.')
    assert(len(tp.statements) == 1)
    st = tp.statements[0]
    assert(isinstance(st, ist.ActiveForm))
    assert(isinstance(st.agent.mods[0], ist.ModCondition))
    assert(st.agent.mods[0].mod_type == 'phosphorylation')
    assert(st.agent.mods[0].residue == 'S')
    assert(st.agent.mods[0].position == '222')

def test_actmods():
    tp = trips.process_text('MEK1 phosphorylated at Ser 218 and Ser222 is activated.')
    assert(len(tp.statements) == 1)
    st = tp.statements[0]
    assert(isinstance(st, ist.ActiveForm))
    assert(isinstance(st.agent.mods[0], ist.ModCondition))
    assert(isinstance(st.agent.mods[1], ist.ModCondition))
    assert(st.agent.mods[0].mod_type == 'phosphorylation')
    assert(st.agent.mods[0].residue == 'S')
    assert(st.agent.mods[0].position == '218')

def test_actmods():
    tp = trips.process_text('BRAF phosphorylated at Ser536 binds MEK1.')
    assert(len(tp.statements) == 1)
    st = tp.statements[0]
    assert(isinstance(st, ist.Complex))
    braf = st.members[0]
    assert(braf.mods[0].mod_type == 'phosphorylation')
    assert(braf.mods[0].residue == 'S')
    assert(braf.mods[0].position == '536')

def test_trips_processor_online():
    """Smoke test to see if imports and executes without error. Doesn't
    check for correctness of parse or of assembled model."""
    tp = trips.process_text('BRAF phosphorylates MEK1 at Ser222.')

def test_trips_processor_offline():
    """Smoke test to see if imports and executes without error. Doesn't
    check for correctness of parse or of assembled model."""
    tp = trips.process_xml(open(test_small_file).read())
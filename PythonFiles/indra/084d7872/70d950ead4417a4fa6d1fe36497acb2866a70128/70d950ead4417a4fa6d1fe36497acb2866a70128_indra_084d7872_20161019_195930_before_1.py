import re
import os
from indra import trips
from indra.statements import *

def process_sentence_xml(sentence):
    fname = re.sub('[^a-zA-Z0-9]', '_', sentence[:-1]) + '.ekb'
    path = os.path.join('trips_ekbs', fname)
    with open(path, 'rb') as fh:
        xml = fh.read().decode('utf-8')
    tp = trips.process_xml(xml)
    return tp

def assert_onestmt(tp):
    assert(tp is not None)
    assert(len(tp.statements) == 1)

def assert_evidence(stmt):
    assert(len(stmt.evidence) == 1)
    assert(stmt.evidence[0].source_api == 'trips')
    assert(stmt.evidence[0].text)

def assert_modtype(stmt, mod_type):
    assert(isinstance(stmt, mod_type))
    assert(stmt.enz is not None)
    assert(stmt.sub is not None)

def test_1():
    sentence = 'The receptor tyrosine kinase EGFR binds the growth factor ligand EGF.'
    tp = process_sentence_xml(sentence)
    assert(tp is not None)
    assert(len(tp.statements) == 1)
    st = tp.statements[0]
    assert(isinstance(st, Complex))
    assert(len(st.members) == 2)
    assert_evidence(st)

def test_2():
    sentence = 'The EGFR-EGF complex binds another EGFR-EGF complex.'
    tp = process_sentence_xml(sentence)
    assert(tp is not None)
    assert(len(tp.statements) == 1)
    st = tp.statements[0]
    assert(isinstance(st, Complex))
    assert(len(st.members) == 2)
    e1, e2 = st.members
    assert(e1.bound_conditions[0].is_bound)
    assert(e2.bound_conditions[0].is_bound)
    assert_evidence(st)

def test_3():
    sentence = 'The EGFR-EGFR complex binds GRB2.'
    tp = process_sentence_xml(sentence)
    assert(tp is not None)
    assert(len(tp.statements) == 1)
    st = tp.statements[0]
    assert(isinstance(st, Complex))
    assert(len(st.members) == 2)
    e, g = st.members
    assert(e.bound_conditions[0].is_bound)
    assert_evidence(st)

def test_4():
    sentence = 'EGFR-bound GRB2 binds SOS1.'
    tp = process_sentence_xml(sentence)
    assert(tp is not None)
    assert(len(tp.statements) == 1)
    st = tp.statements[0]
    assert(isinstance(st, Complex))
    assert(len(st.members) == 2)
    g, s = st.members
    assert(g.bound_conditions[0].is_bound)
    assert_evidence(st)

def test_5():
    sentence = 'GRB2-bound SOS1 binds NRAS that is not bound to BRAF.'
    tp = process_sentence_xml(sentence)
    assert(tp is not None)
    assert(len(tp.statements) == 1)
    st = tp.statements[0]
    assert(isinstance(st, Complex))
    assert(len(st.members) == 2)
    s, n = st.members
    assert(s.bound_conditions[0].is_bound)
    assert(not n.bound_conditions[0].is_bound)
    assert_evidence(st)

def test_6():
    sentence = 'SOS1-bound NRAS binds GTP.'
    tp = process_sentence_xml(sentence)
    assert(tp is not None)
    assert(len(tp.statements) == 1)
    st = tp.statements[0]
    assert(isinstance(st, Complex))
    assert(len(st.members) == 2)
    n, g = st.members
    assert(n.bound_conditions[0].is_bound)
    assert_evidence(st)

def test_7():
    sentence = 'GTP-bound NRAS that is not bound to SOS1 binds BRAF.'
    tp = process_sentence_xml(sentence)
    assert(tp is not None)
    assert(len(tp.statements) == 1)
    st = tp.statements[0]
    assert(isinstance(st, Complex))
    assert(len(st.members) == 2)
    n, b = st.members
    assert(len(n.bound_conditions) == 2)
    assert(n.bound_conditions[0].is_bound)
    assert(not n.bound_conditions[1].is_bound)
    assert_evidence(st)

def test_8():
    sentence = 'Vemurafenib binds BRAF.'
    tp = process_sentence_xml(sentence)
    assert(tp is not None)
    assert(len(tp.statements) == 1)
    st = tp.statements[0]
    assert(isinstance(st, Complex))
    assert(len(st.members) == 2)
    assert_evidence(st)

def test_9():
    sentence = 'BRAF V600E that is not bound to Vemurafenib phosphorylates MAP2K1.'
    tp = process_sentence_xml(sentence)
    assert(tp is not None)
    assert(len(tp.statements) == 1)
    st = tp.statements[0]
    assert(isinstance(st, Phosphorylation))
    assert(st.enz is not None)
    assert(st.sub is not None)
    assert(st.enz.mutations)
    assert(not st.enz.bound_conditions[0].is_bound)
    assert_evidence(st)

def test_10():
    sentence = 'PP2A-alpha dephosphorylates MAP2K1 that is not bound to ERK2.'
    tp = process_sentence_xml(sentence)
    assert(tp is not None)
    assert(len(tp.statements) == 1)
    st = tp.statements[0]
    assert(isinstance(st, Dephosphorylation))
    assert(st.enz is not None)
    assert(st.sub is not None)
    assert(not st.sub.bound_conditions[0].is_bound)
    assert_evidence(st)

def test_11():
    sentence = 'Phosphorylated MAP2K1 is activated.'
    tp = process_sentence_xml(sentence)
    assert(tp is not None)
    assert(len(tp.statements) == 1)
    st = tp.statements[0]
    assert(isinstance(st, ActiveForm))
    assert(st.agent is not None)
    assert(st.agent.mods[0].mod_type == 'phosphorylation')
    assert(st.agent.mods[0].is_modified)
    assert_evidence(st)

def test_12():
    sentence = 'Active MAP2K1 that is not bound to PP2A-alpha phosphorylates ERK2.'
    tp = process_sentence_xml(sentence)
    assert(tp is not None)
    assert(len(tp.statements) == 1)
    st = tp.statements[0]
    assert(isinstance(st, Phosphorylation))
    assert(st.enz is not None)
    assert(st.sub is not None)
    assert(st.sub.active == 'activity')
    assert(not st.sub.bound_conditions[0].is_bound)
    assert_evidence(st)

def test_13():
    sentence = 'DUSP6 dephosphorylates ERK2.'
    tp = process_sentence_xml(sentence)
    assert(tp is not None)
    assert(len(tp.statements) == 1)
    st = tp.statements[0]
    assert(isinstance(st, Dephosphorylation))
    assert(st.enz is not None)
    assert(st.sub is not None)
    assert_evidence(st)

def test_14():
    sentence = 'MAP2K1 ubiquitinates MAPK1.'
    tp = process_sentence_xml(sentence)
    assert_onestmt(tp)
    assert_modtype(tp.statements[0], Ubiquitination)
    assert_evidence(tp.statements[0])

def test_15():
    sentence = 'MAP2K1 ribosylates MAPK1.'
    tp = process_sentence_xml(sentence)
    assert_onestmt(tp)
    assert_modtype(tp.statements[0], Ribosylation)
    assert_evidence(tp.statements[0])

def test_16():
    sentence = 'MAP2K1 hydroxylates MAPK1.'
    tp = process_sentence_xml(sentence)
    assert_onestmt(tp)
    assert_modtype(tp.statements[0], Hydroxylation)
    assert_evidence(tp.statements[0])

def test_17():
    sentence = 'MAP2K1 acetylates MAPK1.'
    tp = process_sentence_xml(sentence)
    assert_onestmt(tp)
    assert_modtype(tp.statements[0], Acetylation)
    assert_evidence(tp.statements[0])

def test_18():
    sentence = 'MAP2K1 farnesylates MAPK1.'
    tp = process_sentence_xml(sentence)
    assert_onestmt(tp)
    assert_modtype(tp.statements[0], Farnesylation)
    assert_evidence(tp.statements[0])

def test_19():
    sentence = 'MAP2K1 deubiquitinates MAPK1.'
    tp = process_sentence_xml(sentence)
    assert_onestmt(tp)
    assert_modtype(tp.statements[0], Deubiquitination)
    assert_evidence(tp.statements[0])

def test_20():
    sentence = 'MAP2K1 deribosylates MAPK1.'
    tp = process_sentence_xml(sentence)
    assert_onestmt(tp)
    assert_modtype(tp.statements[0], Deribosylation)
    assert_evidence(tp.statements[0])

def test_21():
    sentence = 'MAP2K1 dehydroxylates MAPK1.'
    tp = process_sentence_xml(sentence)
    assert_onestmt(tp)
    assert_modtype(tp.statements[0], Dehydroxylation)
    assert_evidence(tp.statements[0])

def test_22():
    sentence = 'MAP2K1 deacetylates MAPK1.'
    tp = process_sentence_xml(sentence)
    assert_onestmt(tp)
    assert_modtype(tp.statements[0], Deacetylation)
    assert_evidence(tp.statements[0])

def test_23():
    sentence = 'MAP2K1 defarnesylates MAPK1.'
    tp = process_sentence_xml(sentence)
    assert_onestmt(tp)
    assert_modtype(tp.statements[0], Defarnesylation)
    assert_evidence(tp.statements[0])

'''
EGF leads to the activation of MAPK1.
Vemurafenib leads to the deactivation of MAPK1.
Stimulation by EGF activates MAPK1.
Treatment with Vemurafenib deactivates MAPK1.
Ubiquitinated MAPK1 is degraded.
MAPK1 is synthesized.
MAP2K1 transcribes MAPK1.
MAP2K1 synthesizes MAPK1.
MAPK1 is degraded.
MAP2K1 degrades MAPK1.
EGFR phosphorylates itself.
EGFR autophosphorylates.
The EGFR-EGFR complex transphosphorylates.
MAPK1 traslocates to the nucleus.
MAPK1 translocates from the nucleus.
MAPK1 translocates from the plasma membrane to the nucleus.
'''
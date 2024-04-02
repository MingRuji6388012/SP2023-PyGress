import os
import json
import requests
import datetime
import unittest
from indra.sources import eidos
from indra.statements import Influence, Association, Event
from indra.assemblers.cag import CAGAssembler
from indra.assemblers.cx import CxAssembler
from indra.assemblers.pysb import PysbAssembler


path_this = os.path.dirname(os.path.abspath(__file__))
test_jsonld = os.path.join(path_this, 'eidos_test.jsonld')


def __get_remote_jsonld():
    res = requests.get('https://raw.githubusercontent.com/clulab/eidos/master/'
                       'example_output/example-0.2.2.jsonld')
    assert res.status_code is 200, "Could not get example json from remote."
    example_json = json.loads(res.content.decode('utf-8'))
    return example_json


def __get_stmts_from_remote_jsonld():
    ex_json = __get_remote_jsonld()
    ep = eidos.process_json(ex_json)
    assert ep is not None, 'Failed to handle json with eidos processor.'
    assert len(ep.statements), 'Did not get statements from json.'
    return ep.statements


def test_process_text():
    ep = eidos.process_text('The cost of fuel decreases water trucking.')
    assert ep is not None
    assert len(ep.statements) == 1
    stmt = ep.statements[0]
    assert isinstance(stmt, Influence)
    assert stmt.subj.concept.name == 'fuel', stmt.subj.concept.name
    assert stmt.obj.concept.name == 'water trucking', stmt.obj.concept.name
    assert stmt.obj.delta.polarity == -1
    assert stmt.evidence[0].annotations['found_by'] == \
        'ported_syntax_1_verb-Causal'
    assert 'TEXT' in stmt.subj.concept.db_refs
    assert 'TEXT' in stmt.obj.concept.db_refs
    # NOTE: groundings are turned off in Travis tests so these are commented
    # out
    # assert 'UN' in stmt.subj.db_refs
    # assert 'UN' in stmt.obj.db_refs
    # assert len(stmt.subj.db_refs['UN']) > 5
    # assert len(stmt.obj.db_refs['UN']) > 5


def test_process_polarity():
    test_jsonld = os.path.join(path_this, 'eidos_neg_event.json')
    ep = eidos.process_json_file(test_jsonld)
    assert ep is not None
    assert len(ep.statements) == 1
    stmt = ep.statements[0]
    assert isinstance(stmt, Influence)
    assert stmt.subj.concept.name == 'fuel', stmt.subj.concept.name
    assert stmt.obj.concept.name == 'water trucking', stmt.obj.concept.name
    assert stmt.obj.delta.polarity == -1
    assert stmt.evidence[0].annotations['found_by'] == \
        'ported_syntax_1_verb-Causal'
    assert 'TEXT' in stmt.subj.concept.db_refs
    assert 'TEXT' in stmt.obj.concept.db_refs


def test_sanitize():
    # Make sure sanitization works
    sanitized = eidos.processor._sanitize('-LRB-something-RRB-')
    assert sanitized == '(something)'


def test_process_json_ld_file():
    ep = eidos.process_json_file(test_jsonld)
    assert len(ep.statements) == 1
    assert 'UN' in ep.statements[0].subj.concept.db_refs
    assert 'UN' in ep.statements[0].obj.concept.db_refs


def test_process_corefs():
    coref_jsonld = os.path.join(path_this, 'eidos_coref.json')
    ep = eidos.process_json_file(coref_jsonld)
    assert ep.doc.coreferences.get('_:Extraction_6') == '_:Extraction_4'
    assert len(ep.statements) == 2
    # Get summaru of subj/objs from statements
    concepts = [(s.subj.concept.name, s.obj.concept.name) for s in
                ep.statements]
    assert ('rainfall', 'flood') in concepts, concepts
    # This ensures that the coreference was successfully resolved
    assert ('flood', 'displacement') in concepts, concepts


def test_process_timex():
    timex_jsonld = os.path.join(path_this, 'eidos_timex.json')
    ep = eidos.process_json_file(timex_jsonld)
    assert len(ep.statements) == 1
    ev = ep.statements[0].evidence[0]
    assert ev.context is None
    subjc = ep.statements[0].subj.context
    assert subjc.__repr__() == subjc.__str__()
    assert subjc.time.duration == 365 * 86400, subjc.time.duration
    assert subjc.time.start == \
        datetime.datetime(year=2018, month=1, day=1, hour=0, minute=0), \
        subjc.time.start
    assert subjc.time.end == \
        datetime.datetime(year=2019, month=1, day=1, hour=0, minute=0), \
        subjc.time.end


def test_process_correlations():
    correl_jsonld = os.path.join(path_this, 'eidos_correlation.json')
    ep = eidos.process_json_file(correl_jsonld)
    assert len(ep.statements) == 1
    st = ep.statements[0]
    assert isinstance(st, Association)
    assert isinstance(st.members[0], Event)
    names = {m.concept.name for m in st.members}
    assert names == {'harvest', 'requirement'}, names


def test_process_negation_hedging():
    nh_jsonld = os.path.join(path_this, 'eidos_neg_hedge.json')
    ep = eidos.process_json_file(nh_jsonld)
    assert len(ep.statements) == 1
    st = ep.statements[0]
    epi = st.evidence[0].epistemics
    assert epi.get('hedgings') == ['may'], epi
    assert epi.get('negated') is True, epi
    annot = st.evidence[0].annotations
    assert annot.get('negated_texts') == ['not']


def test_process_geoids():
    geo_jsonld = os.path.join(path_this, 'eidos_geoid.json')
    ep = eidos.process_json_file(geo_jsonld)
    # Make sure we collect all geoids up front
    ss_loc = {'name': 'South Sudan', 'db_refs': {'GEOID': '7909807'}}
    assert len(ep.doc.geolocs) == 5, len(ep.geoids)
    assert ep.doc.geolocs['_:GeoLocation_1'].to_json() == ss_loc
    # Make sure this event has the right geoid
    assert isinstance(ep.statements[0], Influence)
    ev = ep.statements[1].evidence[0]
    assert ev.context.geo_location.to_json() == ss_loc
    # And that the subject context is captured in annotations
    assert 'subj_context' in ev.annotations, ev.annotations
    assert ev.annotations['subj_context']['geo_location'] == ss_loc


def test_eidos_to_cag():
    stmts = __get_stmts_from_remote_jsonld()
    ca = CAGAssembler()

    # Make sure these don't error
    ca.add_statements(stmts)
    ca.make_model()
    ca.export_to_cytoscapejs()
    return


def test_eidos_to_cx():
    stmts = __get_stmts_from_remote_jsonld()
    cx = CxAssembler()

    # Make sure these don't error
    cx.add_statements(stmts)
    cx.make_model()
    test_fname = 'test_cag_to_cx.cx'
    try:
        cx.save_model(test_fname)
        assert os.path.exists(test_fname), "Failed to create cx file."
    finally:
        if os.path.exists(test_fname):
            os.remove(test_fname)
    return


def test_eidos_to_pysb():
    stmts = __get_stmts_from_remote_jsonld()
    pa = PysbAssembler()

    # Make sure these don't error
    pa.add_statements(stmts)
    model = pa.make_model()
    assert model.rules, model.rules
    for fmt in ['kappa', 'sbml', 'sbgn']:
        exp_str = pa.export_model(fmt)
        assert exp_str, "Got no exported model from eidos->psyb to %s." % fmt
    return


@unittest.skip('Grounding not available on Travis.')
def test_reground_texts():
    er = eidos.reader.EidosReader()
    er.initialize_reader()
    groundings = er.reground_texts(['rainfall', 'hunger'])
    assert groundings[0][0][0] == 'UN/events/weather/precipitation'
    assert groundings[1][0][0] == 'UN/events/human/famine'


def test_standalone_event():
    se_jsonld = os.path.join(path_this, 'eidos_standalone_event.json')
    ep = eidos.process_json_file(se_jsonld)
    assert len(ep.statements) == 1
    st = ep.statements[0]
    assert isinstance(st, Event)
    assert hasattr(st, 'evidence')
    ev = st.evidence[0]
    assert ev.text is not None
    js = st.to_json()
    assert js['evidence']
    from indra.statements import stmts_to_json
    js2 = stmts_to_json([st])[0]
    assert 'evidence' in js2


def test_geoloc_obj():
    se_jsonld = os.path.join(path_this, 'eidos_geoloc_obj.json')
    ep = eidos.process_json_file(se_jsonld)
    st = ep.statements[1]
    ev = st.evidence[0]
    assert not ev.context, ev.context
    assert st.obj.context
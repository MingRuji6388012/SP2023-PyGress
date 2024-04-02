from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str

import os
import unittest
from datetime import datetime
from indra.statements import *
from indra.sources.hume.api import *

# Path to the HUME test files
path_this = os.path.dirname(os.path.abspath(__file__))
test_file_simple = os.path.join(path_this, 'bbn_test_simple.json-ld')
test_file_negatedCause = os.path.join(path_this,
                                      'bbn_test_negatedCause.json-ld')
test_file_negatedEffect = os.path.join(path_this,
                                       'bbn_test_negatedEffect.json-ld')


def test_simple_extraction():
    """Verify that processor extracts a simple causal assertion correctly from
    a JSON-LD file."""
    bp = process_json_file_old(test_file_simple)
    statements = bp.statements

    assert(len(statements) == 1)
    s0 = statements[0]

    assert(isinstance(s0, Influence))
    assert(s0.subj.name == 'cow')
    assert(s0.subj.db_refs['HUME'] == 'Bovine')
    assert(s0.obj.name == 'moo')
    assert(s0.obj.db_refs['HUME'] == 'MooSound')

    assert(len(s0.evidence) == 1)
    ev0 = s0.evidence[0]
    assert(ev0.source_api == 'hume')
    assert(ev0.text == 'Cow causes moo.')


def test_negated_cause():
    """We only want to extract causal relations between two positive events.
    The processor should give no statements for a negated cause."""
    bp = process_json_file_old(test_file_negatedCause)
    assert(len(bp.statements) == 0)


def test_negated_effect():
    """We only want to extract causal relations between two positive events.
    The processor should give no statements for a negated effect."""
    bp = process_json_file_old(test_file_negatedEffect)
    assert(len(bp.statements) == 0)


@unittest.skip('Need updated JSON-LD file')
def test_bbn_on_ben_paragraph():
    bp = process_jsonld_file(os.path.join(path_this,
                                          'hackathon_test_paragraph.json-ld'))
    assert bp is not None
    print(bp.statements)
    stmt_dict = {s.get_hash(shallow=False): s for s in bp.statements}
    assert len(stmt_dict) == 3, len(stmt_dict)


def test_large_bbn_corpus():
    file_path = os.path.join(path_this,
                             'wm_m12.v8.full.v4.json-ld')
    if not os.path.exists(file_path):
        raise unittest.SkipTest("The test file is not available.")
    bp = process_jsonld_file(os.path.join(path_this,
                             'wm_m12.v8.full.v4.json-ld'))
    assert bp is not None
    assert len(bp.statements) > 1000
    print(len(bp.statements))


def test_for_context():
    bp = process_jsonld_file(os.path.join(path_this,
                             'wm_m12.ben_sentence.json-ld'))
    assert bp, "Processor is none."
    assert len(bp.statements) == 1, len(bp.statements)
    stmt = bp.statements[0]
    assert len(stmt.evidence) == 1, len(stmt.evidence)
    ev = stmt.evidence[0]
    assert ev.context is not None
    assert ev.context.time is not None
    time = ev.context.time
    assert time.text == '2018', ev.context.time.text
    assert isinstance(time.start, datetime), type(time.start)
    assert isinstance(time.end, datetime), type(time.end)
    assert isinstance(time.duration, int), type(time.duration)
    assert ev.context.geo_location is not None
    loc = ev.context.geo_location
    assert loc.name == 'South Sudan', loc.name
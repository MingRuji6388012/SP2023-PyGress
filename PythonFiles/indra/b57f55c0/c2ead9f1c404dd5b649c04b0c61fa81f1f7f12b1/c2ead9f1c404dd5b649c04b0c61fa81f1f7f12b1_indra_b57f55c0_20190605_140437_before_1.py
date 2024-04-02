import json
import requests
from os import path
from datetime import datetime

from nose.plugins.attrib import attr

from indra.statements import stmts_from_json, Phosphorylation

BASE = 'http://api.indra.bio:8000/'
HERE = path.dirname(path.abspath(__file__))


def _call_api(method, route, *args, **kwargs):
    route = route.lstrip('/')
    req_meth = getattr(requests, method)
    start = datetime.now()
    print("Submitting request to '%s' at %s." % ('/' + route, start))
    print("\targs:", args)
    print("\tkwargs:", kwargs)
    res = req_meth(BASE + route, *args, **kwargs)
    end = datetime.now()
    print("Got result with %s at %s after %s seconds."
          % (res.status_code, end, (end-start).total_seconds()))
    assert res.status_code == 200, res.status_code
    return res


@attr('webservice')
def test_responsive():
    res = _call_api('get', '')
    assert res.content.startswith(b'This is the INDRA REST API.'), \
        "Unexpected content: %s" % res.content


@attr('webservice')
def test_options():
    res = _call_api('options', '')
    assert res.content == b'{}', \
        "Unexpected content: %s" % res.content


@attr('webservice')
def test_trips_process_text():
    res = _call_api('post', 'trips/process_text',
                    json={'text': 'MEK phosphorylates ERK.'})
    res_json = res.json()
    assert 'statements' in res_json.keys(), res_json
    print(res_json.keys())
    stmts = stmts_from_json(res_json['statements'])
    assert len(stmts) == 1, len(stmts)
    stmt = stmts[0]
    assert isinstance(stmt, Phosphorylation), type(stmt)
    assert stmt.enz.name == 'MEK', stmt.enz
    assert stmt.sub.name == 'ERK', stmt.sub


@attr('webservice')
def test_trips_process_xml():
    with open(path.join(HERE, 'test_trips_ekb.xml'), 'r') as f:
        xml_str = f.read()
    res = _call_api('post', 'trips/process_xml', json={'xml_str': xml_str})
    res_json = res.json()
    assert 'statements' in res_json.keys(), res_json
    print(res_json.keys())
    stmts = stmts_from_json(res_json['statements'])
    assert len(stmts) == 1, len(stmts)
    stmt = stmts[0]
    assert isinstance(stmt, Phosphorylation), type(stmt)
    assert stmt.enz.name == 'MEK', stmt.enz
    assert stmt.sub.name == 'ERK', stmt.sub


@attr('webservice')
def test_reach_process_text():
    res = _call_api('post', 'reach/process_text',
                    json={'text': 'MEK phosphorylates ERK.'})
    res_json = res.json()
    assert 'statements' in res_json.keys(), res_json
    print(res_json.keys())
    stmts = stmts_from_json(res_json['statements'])
    assert len(stmts) == 1, len(stmts)
    stmt = stmts[0]
    assert isinstance(stmt, Phosphorylation), type(stmt)
    assert stmt.enz.name == 'MEK', stmt.enz
    assert stmt.sub.name == 'ERK', stmt.sub


@attr('webservice')
def test_reach_process_json():
    # TODO: Add test of reach process json
    return


@attr('webservice')
def test_reach_process_pmcid():
    res = _call_api('post', 'reach/process_pmc', json={'pmcid': 'PMC1234335'})
    res_json = res.json()
    print(json.dumps(res_json, indent=2))
    assert len(res_json['statements']), len(res_json['statements'])


STMT_JSON = {
    "id": "acc6d47c-f622-41a4-8ae9-d7b0f3d24a2f",
    "type": "Complex",
    "members": [
        {"db_refs": {"TEXT": "MEK", "FPLX": "MEK"}, "name": "MEK"},
        {"db_refs": {"TEXT": "ERK", "FPLX": "ERK"}, "name": "ERK"}
    ],
    "sbo": "http://identifiers.org/sbo/SBO:0000526",
    "evidence": [{"text": "MEK binds ERK", "source_api": "trips"}]
}


@attr('webservice')
def test_assemblers_cyjs():
    stmt_str = json.dumps({'statements': [STMT_JSON]})
    res = _call_api('post', 'assemblers/cyjs', stmt_str)
    res_json = res.json()
    assert len(res_json['edges']) == 1, len(res_json['edges'])
    assert len(res_json['nodes']) == 2, len(res_json['nodes'])
    return


@attr('webservice')
def test_assemblers_pysb_no_format():
    stmt_str = json.dumps({'statements': [STMT_JSON]})
    res = _call_api('post', 'assemblers/pysb', stmt_str)
    res_json = res.json()
    assert 'model' in res_json.keys()
    return
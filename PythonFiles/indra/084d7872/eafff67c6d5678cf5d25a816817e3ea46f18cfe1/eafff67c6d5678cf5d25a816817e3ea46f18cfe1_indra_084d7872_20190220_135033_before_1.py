import json
import copy
import logging
import unittest
from indra.statements import *
from indra.tools.live_curation import app, curator, Corpus, LiveCurator


logger = logging.getLogger(__name__)


def _make_corpus():
    ev1 = Evidence(source_api='eidos', text='A',
                   annotations={'found_by': 'ported_syntax_1_verb-Causal'})
    ev2 = Evidence(source_api='eidos', text='B',
                   annotations={'found_by': 'dueToSyntax2-Causal'})
    ev3 = Evidence(source_api='hume', text='C')
    ev4 = Evidence(source_api='cwms', text='D')
    ev5 = Evidence(source_api='sofia', text='E')
    ev6 = Evidence(source_api='sofia', text='F')
    stmt1 = Influence(Concept('x'), Concept('y'), evidence=[ev1, ev2])
    stmt2 = Influence(Concept('x'), Concept('y'), evidence=[ev1, ev3])
    stmt3 = Influence(Concept('x'), Concept('y'), evidence=[ev3, ev4, ev5])
    stmt4 = Influence(Concept('x'), Concept('y'), evidence=[ev5])
    stmt5 = Influence(Concept('x'), Concept('y'), evidence=[ev6])
    stmt1.uuid = '1'
    stmt2.uuid = '2'
    stmt3.uuid = '3'
    stmt4.uuid = '4'
    stmt5.uuid = '5'
    stmts = [stmt1, stmt2, stmt3, stmt4]
    raw_stmts = copy.deepcopy(stmts)
    return Corpus(statements=stmts, raw_statements=raw_stmts)


def test_no_curation():
    curator = LiveCurator(corpora={'1': _make_corpus()})
    curator.submit_curation(corpus_id='1', curations={})
    beliefs = curator.update_beliefs(corpus_id='1')
    expected = {'1': 0.91675,
                '2': 0.8968,
                '3': 0.957125,
                '4': 0.65,
                '5': 0.65}
    assert close_enough(beliefs, expected), (beliefs, expected)


def test_eid_rule1_incorrect():
    curator = LiveCurator(corpora={'1': _make_corpus()})
    curator.submit_curation(corpus_id='1', curations={'1': 0})
    expected = {'1': 0,
                '2': 0.8942,
                '3': 0.957125,
                '4': 0.65,
                '5': 0.65}
    beliefs = curator.update_beliefs(corpus_id='1')
    assert close_enough(beliefs, expected), (beliefs, expected)

    # Submit another curation
    curator.submit_curation(corpus_id='1', curations={'1': 0})
    expected = {'1': 0,
                '2': 0.8917,
                '3': 0.957125,
                '4': 0.65,
                '5': 0.65}
    beliefs = curator.update_beliefs(corpus_id='1')
    assert close_enough(beliefs, expected), (beliefs, expected)


def test_eid_rule1_correct():
    curator = LiveCurator(corpora={'1': _make_corpus()})
    curator.submit_curation(corpus_id='1', curations={'1': 1})
    expected = {'1': 1,
                '2': 0.8979,
                '3': 0.957125,
                '4': 0.65,
                '5': 0.65}
    beliefs = curator.update_beliefs(corpus_id='1')
    assert close_enough(beliefs, expected), (beliefs, expected)


def test_eid_rule2_correct():
    curator = LiveCurator(corpora={'1': _make_corpus()})
    curator.submit_curation(corpus_id='1', curations={'2': 1})
    expected = {'1': 0.91717,
                '2': 1,
                '3': 0.95916,
                '4': 0.65,
                '5': 0.65}
    beliefs = curator.update_beliefs(corpus_id='1')
    assert close_enough(beliefs, expected), (beliefs, expected)


def test_hume_incorrect():
    curator = LiveCurator(corpora={'1': _make_corpus()})
    curator.submit_curation(corpus_id='1', curations={'3': 0})
    expected = {'1': 0.91675,
                '2': 0.88772,
                '3': 0,
                '4': 0.61904,
                '5': 0.61904}
    beliefs = curator.update_beliefs(corpus_id='1')
    assert close_enough(beliefs, expected), (beliefs, expected)


def test_sofia_incorrect():
    curator = LiveCurator(corpora={'1': _make_corpus()})
    curator.submit_curation(corpus_id='1', curations={'4': 0})
    expected = {'1': 0.91675,
                '2': 0.89684,
                '3': 0.95333,
                '4': 0.0,
                '5': 0.61904}
    beliefs = curator.update_beliefs(corpus_id='1')
    assert close_enough(beliefs, expected), (beliefs, expected)

    curator.submit_curation(corpus_id='1', curations={'5': 0})
    expected = {'1': 0.91675,
                '2': 0.89684,
                '3': 0.94988,
                '4': 0,
                '5': 0}
    beliefs = curator.update_beliefs(corpus_id='1')
    assert close_enough(beliefs, expected), (beliefs, expected)


class LiveCurationTestCase(unittest.TestCase):
    def setUp(self):
        _make_corpus()
        app.testing = True
        self.app = app.test_client()
        curator.corpora = {'1': _make_corpus()}

    def _send_request(self, endpoint, req_dict):
        resp = self.app.post(endpoint,
                             data=json.dumps(req_dict),
                             headers={'Content-Type': 'application/json'})
        return resp

    def _reset_scorer(self):
        resp = self.app.post('reset_curation',
                             data='{}',
                             headers={'Content-Type': 'application/json'})
        assert resp.status_code == 200, resp

    # Tests ==================
    def test_alive(self):
        resp = self._send_request('submit_curation', {'corpus_id': '1'})
        assert resp.status_code == 200, resp

    def test_bad_corpus(self):
        resp = self._send_request('submit_curation', {'corpus_id': '2'})
        assert resp.status_code == 400, resp

    def test_no_curation(self):
        self._reset_scorer()
        self._send_request('submit_curation', {'corpus_id': '1'})
        resp = self._send_request('update_beliefs', {'corpus_id': '1'})
        res = json.loads(resp.data.decode('utf-8'))
        expected = {'1': 0.91675,
                    '2': 0.8968,
                    '3': 0.957125,
                    '4': 0.65,
                    '5': 0.65}
        assert close_enough(res, expected), (res, expected)

    def test_eid_rule1_incorrect(self):
        self._reset_scorer()
        self._send_request('submit_curation', {'corpus_id': '1',
                                               'curations': {'1': 0}})
        resp = self._send_request('update_beliefs', {'corpus_id': '1'})
        assert resp.status_code == 200
        res = json.loads(resp.data.decode('utf-8'))
        expected = {'1': 0,
                    '2': 0.8942,
                    '3': 0.957125,
                    '4': 0.65,
                    '5': 0.65}
        assert close_enough(res, expected), (res, expected)

    def test_eid_rule1_incorrect_again(self):
        self._reset_scorer()
        self._send_request('submit_curation', {'corpus_id': '1',
                                               'curations': {'1': 0}})
        self._send_request('submit_curation', {'corpus_id': '1',
                                               'curations': {'1': 0}})
        resp = self._send_request('update_beliefs', {'corpus_id': '1'})
        assert resp.status_code == 200, resp
        res = json.loads(resp.data.decode('utf-8'))
        expected = {'1': 0,
                    '2': 0.8917,
                    '3': 0.957125,
                    '4': 0.65,
                    '5': 0.65}
        assert close_enough(res, expected), (res, expected)

    def test_eid_rule1_correct(self):
        self._reset_scorer()
        self._send_request('submit_curation', {'corpus_id': '1',
                                               'curations': {'1': 1}})
        resp = self._send_request('update_beliefs', {'corpus_id': '1'})
        assert resp.status_code == 200
        res = json.loads(resp.data.decode('utf-8'))
        expected = {'1': 1,
                    '2': 0.8979,
                    '3': 0.957125,
                    '4': 0.65,
                    '5': 0.65}
        assert close_enough(res, expected), (res, expected)

    def test_eid_rule2_correct(self):
        self._reset_scorer()
        self._send_request('submit_curation', {'corpus_id': '1',
                                               'curations': {'2': 1}})
        resp = self._send_request('update_beliefs', {'corpus_id': '1'})
        assert resp.status_code == 200
        res = json.loads(resp.data.decode('utf-8'))
        expected = {'1': 0.91717,
                    '2': 1,
                    '3': 0.95916,
                    '4': 0.65,
                    '5': 0.65}
        assert close_enough(res, expected), (res, expected)

    def test_hume_incorrect(self):
        self._reset_scorer()
        self._send_request('submit_curation', {'corpus_id': '1',
                                                'curations': {'3': 0}})
        resp = self._send_request('update_beliefs', {'corpus_id': '1'})
        assert resp.status_code == 200
        res = json.loads(resp.data.decode('utf-8'))
        expected = {'1': 0.91675,
                    '2': 0.88772,
                    '3': 0,
                    '4': 0.61904,
                    '5': 0.61904}
        assert close_enough(res, expected), (res, expected)

    def test_sofia_incorrect(self):
        self._reset_scorer()
        self._send_request('submit_curation', {'corpus_id': '1',
                                               'curations': {'4': 0}})
        resp = self._send_request('update_beliefs', {'corpus_id': '1'})
        assert resp.status_code == 200
        res = json.loads(resp.data.decode('utf-8'))
        expected = {'1': 0.91675,
                    '2': 0.89684,
                    '3': 0.95333,
                    '4': 0.0,
                    '5': 0.61904}
        assert close_enough(res, expected), (res, expected)
        self._send_request('submit_curation', {'corpus_id': '1',
                                               'curations': {'5': 0}})
        resp = self._send_request('update_beliefs', {'corpus_id': '1'})
        assert resp.status_code == 200
        res = json.loads(resp.data.decode('utf-8'))
        expected = {'1': 0.91675,
                    '2': 0.89684,
                    '3': 0.94988,
                    '4': 0,
                    '5': 0}
        assert close_enough(res, expected), (res, expected)

    def test_add_ontology_node(self):
        self._send_request('add_ontology_entry',
                           {'entry': 'UN/animal/dog',
                            'examples': ['canine', 'dog', 'puppy']})
        self._send_request('update_groundings', {'corpus_id': '1'})


def close_enough(probs, ref):
    for k, v in probs.items():
        if abs(ref[k] - probs[k]) > 0.0001:
            logger.error('%s: %.4f != %.4f' % (k, probs[k], ref[k]))
            return False
    return True


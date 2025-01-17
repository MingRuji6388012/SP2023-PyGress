import json
import jsonschema
import os
from nose.tools import assert_raises
from jsonschema.exceptions import ValidationError

dir_this = os.path.dirname(__file__)
schema_file = os.path.join(dir_this, '../../schemas/statements_schema.json')
with open(schema_file, 'r') as f:
    schema = json.loads(f.read())

valid_agent1 = {'name': 'RAF', 'db_refs': {'TEXT': 'RAF'}}
valid_agent2 = {'name': 'RAS', 'db_refs': {'TEXT': 'RAS'}}
valid_agent3 = {'name': 'ERK', 'db_refs': {'TEXT': 'ERK'}}

invalid_agent1 = {'name': 'RAS', 'db_refs': 2}
invalid_agent2 = {'db_refs': {'TEXT': 'RAS'}}
invalid_agent3 = {'name': 'cow', 'db_refs': {'TEXT': 'RAS'},
                  'bound_conditions': 'mooooooooooo!'}

valid_concept1 = {'name': 'government', 'db_refs': {'TEXT': 'government'}}
valid_concept2 = {'name': 'agriculture', 'db_refs': {'TEXT': 'agriculture'}}

invalid_concept1 = {'name': 3, 'db_refs': {'TEXT': 'government'}}
invalid_concept2 = {'name': 'government'}


def val(s):
    jsonschema.validate([s], schema)


def test_valid_modification():
    # Calls to validate() in this function should not raise exceptions
    mod_types = ['Phosphorylation', 'Dephosphorylation', 'Ubiquitination',
                 'Deubiquitination', 'Sumoylation', 'Desumoylation',
                 'Hydroxylation', 'Dehydroxylation', 'Acetylation',
                 'Deacetylation', 'Glycosylation', 'Deglycosylation',
                 'Farnesylation', 'Defarnesylation', 'Geranylgeranylation',
                 'Degeranylgeranylation', 'Palmitoylation', 'Depalmitoylation',
                 'Myristoylation', 'Demyristoylation', 'Ribosylation',
                 'Deribosylation', 'Methylation', 'Demethylation',
                 'Activation', 'Inhibition']

    for mod_type in mod_types:
        s = {'enz': valid_agent1, 'sub': valid_agent2,
             'type': mod_type, 'id': '5'}
        jsonschema.validate([s], schema)

        if mod_type not in ['Activation', 'Inhibition']:
            s['residue'] = 'S'
            jsonschema.validate([s], schema)

            s['position'] = '10'
            jsonschema.validate([s], schema)


def test_invalid_phosphorylation():
    s = {'enz': valid_agent1, 'sub': valid_agent2, 'type': 'Phosphorylation',
         'id': '5', 'residue': 5}  # residue should be a string
    assert_raises(ValidationError, val, s)

    s = {'enz': valid_agent1, 'sub': invalid_agent1, 'type': 'Phosphorylation',
         'id': '5'}
    assert_raises(ValidationError, val, s)

    s = {'enz': valid_agent1, 'sub': invalid_agent2, 'type': 'Phosphorylation',
         'id': '5'}
    assert_raises(ValidationError, val, s)

    s = {'enz': valid_agent1, 'sub': invalid_agent3, 'type': 'Phosphorylation',
         'id': '5'}
    assert_raises(ValidationError, val, s)

    invalid_evidence = {'source_api': 42}
    s = {'enz': valid_agent1, 'sub': valid_agent2, 'type': 'Phosphorylation',
         'id': '5', 'evidence': invalid_evidence}


def test_valid_active_form():
    s = {'agent': valid_agent1, 'activity': 'kinase', 'is_active': True,
         'type': 'ActiveForm', 'id': '6'}
    jsonschema.validate([s], schema)


def test_invalid_active_form():
    s = {'agent': invalid_agent1, 'activity': 'kinase', 'is_active': True,
         'type': 'ActiveForm', 'id': '6'}
    assert_raises(ValidationError, val, s)

    s = {'agent': valid_agent1, 'activity': 'kinase', 'is_active': 'moo',
         'type': 'ActiveForm', 'id': '6'}
    assert_raises(ValidationError, val, s)

    s = {'agent': valid_agent1, 'activity': 'kinase', 'is_active': True,
         'type': 'ActiveForm', 'id': 42}
    assert_raises(ValidationError, val, s)

    s = {'agent': valid_agent1, 'activity': 'kinase', 'is_active': True,
         'type': 'MOO', 'id': '6'}
    assert_raises(ValidationError, val, s)

    s = {'agent': valid_agent1, 'activity': {'cow': False}, 'is_active': True,
         'type': 'ActiveForm', 'id': '6'}
    assert_raises(ValidationError, val, s)


def test_valid_complex():
    s = {'members': [valid_agent1, valid_agent2], 'type': 'Complex', 'id': '3'}
    jsonschema.validate([s], schema)

    s = {'members': [], 'type': 'Complex', 'id': '3'}
    jsonschema.validate([s], schema)


def test_invalid_complex():
    s = {'members': [invalid_agent1, valid_agent2], 'type': 'Complex',
         'id': '3'}
    assert_raises(ValidationError, val, s)

    s = {'members': [valid_agent1, invalid_agent2], 'type': 'Complex',
         'id': '3'}
    assert_raises(ValidationError, val, s)


def test_valid_influence():
    s = {'subj': valid_concept1, 'obj': valid_concept2, 'subj_delta': None,
         'obj_delta': None, 'type': 'Influence', 'id': '10'}
    jsonschema.validate([s], schema)


def test_invalid_influence():
    s = {'subj': invalid_concept1, 'obj': valid_concept2, 'subj_delta': None,
         'obj_delta': None, 'type': 'Influence', 'id': '10'}
    assert_raises(ValidationError, val, s)

    s = {'subj': valid_concept1, 'obj': invalid_concept2, 'subj_delta': None,
         'obj_delta': None, 'type': 'Influence', 'id': '10'}
    assert_raises(ValidationError, val, s)

    s = {'subj': valid_concept1, 'obj': valid_concept2, 'subj_delta': None,
         'obj_delta': 'Henry', 'type': 'Influence', 'id': '10'}
    assert_raises(ValidationError, val, s)

    s = {'subj': valid_concept1, 'obj': valid_concept2, 'subj_delta': 'Larry',
         'obj_delta': None, 'type': 'Influence', 'id': '10'}
    assert_raises(ValidationError, val, s)

    s = {'subj': valid_concept1, 'obj': valid_concept2, 'subj_delta': None,
         'obj_delta': None, 'type': 'Influence', 'id': 10}
    assert_raises(ValidationError, val, s)


def test_valid_conversion():
    s = {'type': 'Conversion', 'id': '11', 'subj': valid_agent1,
         'obj_from': [valid_agent2, valid_agent3], 'obj_to': [valid_agent3]}
    jsonschema.validate([s], schema)


def test_invalid_conversion():
    s = {'type': 'Conversion', 'id': '11', 'subj': valid_agent1,
         'obj_from': [12, valid_agent3], 'obj_to': [valid_agent3]}
    assert_raises(ValidationError, val, s)

    s = {'type': 'Conversion', 'id': '11', 'subj': valid_agent1,
         'obj_from': [valid_agent2, valid_agent3],
         'obj_to': [valid_agent3, 12]}
    assert_raises(ValidationError, val, s)

    s = {'type': 'Conversion', 'id': '11', 'subj': 'dog',
         'obj_from': [valid_agent2, valid_agent3], 'obj_to': [valid_agent3]}
    assert_raises(ValidationError, val, s)

    s = {'type': 'Conversion', 'id': '11', 'subj': valid_agent1,
         'obj_from': 'banana', 'obj_to': [valid_agent3]}
    assert_raises(ValidationError, val, s)


def test_self_modifications():
    self_mods = ['Autophosphorylation', 'Transphosphorylation']
    for self_mod in self_mods:
        s = {'type': self_mod, 'id': '20', 'enz': valid_agent1}
        jsonschema.validate([s], schema)

        s['residue'] = 'S'
        jsonschema.validate([s], schema)

        s['position'] = '10'
        jsonschema.validate([s], schema)


def test_translocation():
    s = {'type': 'Translocation', 'id': '30', 'agent': valid_agent1}
    jsonschema.validate([s], schema)

    s['from_location'] = 'A'
    jsonschema.validate([s], schema)

    s['to_location'] = 'B'
    jsonschema.validate([s], schema)

    s['to_location'] = 3
    assert_raises(ValidationError, val, s)


def test_gef():
    s = {'type': 'Gef', 'id': '40', 'agent': valid_agent1, 'ras': valid_agent2}
    jsonschema.validate([s], schema)


def test_gap():
    s = {'type': 'Gap', 'id': '41', 'gap': valid_agent1, 'ras': valid_agent2}
    jsonschema.validate([s], schema)

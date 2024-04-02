import json
import jsonschema
import os
from nose.tools import assert_raises

dir_this = os.path.dirname(__file__)
schema_file = os.path.join(dir_this, '../../schemas/statements_schema.json')
with open(schema_file, 'r') as f:
    schema = json.loads(f.read())

valid_agent1 = {'name': 'RAF', 'db_refs': {'TEXT': 'RAF'}}
valid_agent2 = {'name': 'RAS', 'db_refs': {'TEXT': 'RAS'}}

invalid_agent1 = {'name': 'RAS', 'db_refs': 2}
invalid_agent2 = {'db_refs': {'TEXT': 'RAS'}}
invalid_agent3 = {'name': 'cow', 'db_refs': {'TEXT': 'RAS'}, 'bound_conditions': 'mooooooooooo!'}

def test_valid_phosphorylation():
    # Calls to validate() in this function should not raise exceptions
    s = {'enz': valid_agent1, 'sub': valid_agent2, 'type': 'Phosphorylation', 'id': '5'}
    jsonschema.validate([s], schema)
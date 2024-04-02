from indra.databases import biogrid_client
from indra.util import unicode_strs

def test_biogrid_request():
    results = biogrid_client._send_request(['MAP2K1', 'MAPK1'])
    assert unicode_strs(results)
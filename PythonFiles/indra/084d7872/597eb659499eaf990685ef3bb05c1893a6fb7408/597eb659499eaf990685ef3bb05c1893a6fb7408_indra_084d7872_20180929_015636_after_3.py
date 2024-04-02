from __future__ import absolute_import, print_function, unicode_literals

from nose.plugins.attrib import attr
from indra.databases.lincs_client import get_drug_target_data
from indra.sources.lincs_drug import process_from_web


@attr('webservice')
def test_process_from_web():
    lincs_p = process_from_web()
    assert lincs_p is not None
    assert lincs_p.statements
    data_len = len(get_drug_target_data())
    num_stmts = len(lincs_p.statements)
    assert num_stmts == data_len, \
        ("Did not convert all statements: expected %d, got %d."
         % (data_len, num_stmts))
    assert all(len(s.evidence) > 0 for s in lincs_p.statements),\
        "Some statements lack evidence."

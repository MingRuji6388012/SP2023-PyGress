from belpy.biopax import biopax_api
from belpy.pysb_assembler import PysbAssembler

def test_hyphenated_agent_names():
    """This query should contain reactions with agent names RAF1-BRAF,
    which need to be canonicalized to Python-compatible names before
    model assembly."""
    bp = biopax_api.process_pc_neighborhood(['BRAF'])
    bp.get_phosphorylation()
    pa = PysbAssembler()
    pa.add_statements(bp.statements)
    pa.make_model()
import pickle
from indra.assemblers.pysb import PysbAssembler


def get_subnetwork(statements, nodes):
    """Return a PySB model based on a subset of given INDRA Statements.

    Statements are first filtered for nodes in the given list and other nodes
    are optionally added based on relevance in a given network. The filtered
    statements are then assembled into an executable model using INDRA's
    PySB Assembler.

    Parameters
    ----------
    statements : list[indra.statements.Statement]
        A list of INDRA Statements to extract a subnetwork from.
    nodes : list[str]
        The names of the nodes to extract the subnetwork for.

    Returns
    -------
    model : pysb.Model
        A PySB model object assembled using INDRA's PySB Assembler from
        the INDRA Statements corresponding to the subnetwork.
    """
    filtered_statements = _filter_statements(statements, nodes)
    pa = PysbAssembler()
    pa.add_statements(filtered_statements)
    model = pa.make_model()
    return model


def _filter_statements(statements, agents):
    """Return INDRA Statements which have Agents in the given list.

    Only statements are returned in which all appearing Agents as in the
    agents list.

    Parameters
    ----------
    statements : list[indra.statements.Statement]
        A list of INDRA Statements to filter.
    agents : list[str]
        A list of agent names that need to appear in filtered statements.

    Returns
    -------
    filtered_statements : list[indra.statements.Statement]
        The list of filtered INDRA Statements.
    """
    filtered_statements = []
    for s in statements:
        if all([a is not None for a in s.agent_list()]) and \
            all([a.name in agents for a in s.agent_list()]):
            filtered_statements.append(s)
    return filtered_statements


if __name__ == '__main__':
    genes = ['EGF', 'EGFR', 'ERBB2', 'GRB2', 'SOS1', 'HRAS', 'RAF1',
             'MAP2K1', 'MAPK1']

    with open('models/rasmachine/rem/model.pkl', 'rb') as f:
        model = pickle.load(f)
    stmts = []
    for k, v in model.items():
        stmts += v

    model = get_subnetwork(stmts, genes)


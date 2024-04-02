import pybel.constants as pc
from indra.statements import *
from indra.databases import hgnc_client, uniprot_client

def process_pybel_graph(graph):
    proc = PybelProcessor(graph)
    proc.get_statements()
    return proc


class PybelProcessor(object):
    """Extract INDRA Statements from a PyBEL Graph.

    Parameters
    ----------
    graph : pybel.BELGraph
        PyBEL graph containing the BEL content.

    Attributes
    ----------
    statements : list[indra.statements.Statement]
        A list of extracted INDRA Statements representing BEL Statements.
    """
    def __init__(self, graph):
        self.graph = graph


    def get_statements(self):
        for u, v, d in self.graph.edges_iter(data=True):
            u_data = self.graph.node[u]
            v_data = self.graph.node[v]

            if v_data[pc.FUNCTION] == pc.PROTEIN and \
               d[pc.RELATION] in pc.CAUSAL_RELATIONS:
                stmt = self._get_regulate_amount(u_data, v_data, d)

        st = Phosphorylation(Agent('A'), Agent('B'))
        self.statements = [st]

    def _get_regulate_amount(self, u_data, v_data, edge_data):
        is_direct = _rel_is_direct(d)
        subj = _get_agent(u_data)
        #stmt = IncreaseAmount(


def _get_agent(node_data):
    name = node_data.get(pc.NAME)
    ns = node_data[pc.NAMESPACE]
    ident = node_data.get(pc.IDENTIFIER)
    # No ID present, get identifier using the name, namespace
    db_refs = None
    if not ident:
        assert name, "Node must have a name if lacking an identifier."
        if ns == 'HGNC':
            hgnc_id = hgnc_client.get_hgnc_id(name)
            if not hgnc_id:
                raise ValueError("Invalid HGNC name: %s" % name)
            db_refs = {'HGNC': hgnc_id, 'UP': _get_up_id(hgnc_id)}
    # We've already got an identifier, look up other identifiers if necessary
    else:
        # Get the name, overwriting existing name if necessary
        if ns == 'HGNC':
            name = hgnc_client.get_hgnc_name(ident)
            db_refs = {'HGNC': ident, 'UP': _get_up_id(ident)}
        elif ns == 'UP':
            db_refs = {'UP': ident}
            name = uniprot_client.get_gene_name(ident)
            assert name
            if uniprot_client.is_human(ident):
                hgnc_id = hgnc_client.get_hgnc_id(name)
                if not hgnc_id:
                    logger.info('Uniprot ID linked to invalid human gene '
                                'name %s' % name)
                else:
                    db_refs['HGNC'] = hgnc_id
    if db_refs is None:
        raise ValueError('Unable to get identifier information for node: %s'
                         % node_data)
    # Get modification conditions
    mods = []
    muts = []
    if pc.VARIANTS in node_data:
        variants = node_data[pc.VARIANTS]
        for var in variants:
            if var[pc.KIND] == pc.HGVS:
                pass
            elif var[pc.KIND] == pc.PMOD:
                var_id_dict = var[pc.IDENTIFIER]
                var_ns = var_id_dict[pc.NAMESPACE]
                if var_ns == pc.BEL_DEFAULT_NAMESPACE:
                    var_id = var_id_dict[pc.NAME]
                    mod_type = _pybel_indra_pmod_map.get(var_id)
                    if mod_type is None:
                        logger.info("Unhandled modification type %s (%s)" %
                                    (var_id, node_data))
                        continue
                    mc = ModCondition(mod_type, var.get(pc.PMOD_CODE),
                                      var.get(pc.PMOD_POSITION))
                    mods.append(mc)
            elif var[pc.KIND] == pc.GMOD:
                logger.debug('Unhandled node variant GMOD: %s' % node_data)
            elif var[pc.KIND] == pc.FRAG:
                logger.debug('Unhandled node variant FRAG: %s' % node_data)
            else:
                logger.debug('Unknown node variant type: %s' % node_data)
    ag = Agent(name, db_refs=db_refs, mods=mods)
    return ag



    # name
    # namespace
    # identifier

    # INDRA:
    # name
    # db_refs
    # conditions: muts, mods, bound_conds, loc_conds, activity

def _rel_is_direct(d):
    return d[pc.RELATION] in (pc.DIRECTLY_INCREASES, pc.DIRECTLY_DECREASES)


def _get_up_id(hgnc_id):
    up_id = hgnc_client.get_uniprot_id(hgnc_id)
    if not up_id:
        raise ValueError("No Uniprot ID for HGNC ID %s" % hgnc_id)
    return up_id


_pybel_indra_pmod_map = {
    'Ph': 'phosphorylation',
    'Hy': 'hydroxylation',
    'Sumo': 'sumoylation',
    'Ac': 'acetylation',
    'Glyco': 'glycosylation',
    'ADPRib': 'ribosylation',
    'Ub': 'ubiquitination',
    'Farn': 'farnesylation',
    'Gerger': 'geranylgeranylation',
    'Palm': 'palmitoylation',
    'Myr': 'myristoylation',
    'Me': 'methylation',
}
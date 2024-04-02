import logging
from copy import copy
import pybel.constants as pc
from pybel.struct import node_has_pmod
from indra.statements import *
from indra.databases import hgnc_client, uniprot_client
from indra.assemblers.pybel_assembler import _pybel_indra_act_map


logger = logging.getLogger('pybel_processor')


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
        self.statements = []

    def get_statements(self):
        graph_nodes = set()
        for u, v, d in self.graph.edges_iter(data=True):
            if d[pc.RELATION] not in pc.CAUSAL_RELATIONS:
                continue
            # Add nodes to the node set
            graph_nodes.add(u)
            graph_nodes.add(v)
            u_data = self.graph.node[u]
            v_data = self.graph.node[v]
            subj_activity = _get_activity_condition(d.get(pc.SUBJECT))
            obj_activity = _get_activity_condition(d.get(pc.OBJECT))
            # Modification, e.g.
            #   x(Foo) -> p(Bar, pmod(Ph))
            #   act(x(Foo)) -> p(Bar, pmod(Ph))
            if v_data[pc.FUNCTION] == pc.PROTEIN and \
               node_has_pmod(self.graph, v):
                self._get_modification(u_data, v_data, d)
            elif obj_activity:
                # If the agents on the left and right hand sides are the same,
                # then get an active form:
                # ActiveForm
                #   p(Foo, {variants}) ->/-| act(p(Foo))
                # Also Composite active forms:
                #   compositeAbundance(p(Foo, pmod('Ph', 'T')),
                #                       p(Foo, pmod('Ph', 'Y'))) ->/-|
                #                            act(p(Foo))
                if not subj_activity and _proteins_match(u_data, v_data):
                    self._get_active_form(u_data, v_data, d)
                # Activation/Inhibition
                #   x(Foo) -> act(x(Foo))
                #   act(x(Foo)) -> act(x(Foo))
                else:
                    self._get_regulate_activity(u_data, v_data, d)
            # Regulate amount
            #   x(Foo) -> p(Bar)
            #   x(Foo) -> r(Bar)
            #   act(x(Foo)) -> p(Bar):
            #   x(Foo) -> deg(p(Bar))
            #   act(x(Foo)) ->/-| deg(p(Bar))
            elif v_data[pc.FUNCTION] in (pc.PROTEIN, pc.RNA) and \
                 not obj_activity:
                self._get_regulate_amount(u_data, v_data, d)
            # Gef
            #   act(p(Foo)) => gtp(p(Foo))
            # Gap
            #   act(p(Foo)) =| gtp(p(Foo))
            # GtpActivation
            #   gtp(p(Foo)) => act(p(Foo))


            # Conversion
            #   rxn(reactants(r1,...,rn), products(p1,...pn))
            #   x(Foo) -> rxn(reactants(r1,...,rn), products(p1,...pn))
            #   act(x(Foo)) -> rxn(reactants(r1,...,rn), products(p1,...pn))

            # Complex(a,b) -> asdfasdf
            # p(A, pmod('ph')) -> Complex(A, B)
            #            Complex(A-Ph, B) 


            # Complexes
            #   complex(x(Foo), x(Bar), ...)

    def _get_regulate_amount(self, u_data, v_data, edge_data):
        subj_agent = _get_agent(u_data, edge_data.get(pc.SUBJECT))
        obj_agent = _get_agent(v_data, edge_data.get(pc.OBJECT))
        # FIXME: If an RNA agent type, create a transcription-specific
        # Statement
        if subj_agent is None or obj_agent is None:
            return
        # FIXME: If object is a degradation, create a stability-specific
        # Statement
        obj_mod = edge_data.get(pc.OBJECT)
        deg_polarity = (-1 if obj_mod and obj_mod[pc.MODIFIER] == pc.DEGRADATION
                           else 1)
        rel_polarity = (1 if edge_data[pc.RELATION] in
                                    pc.CAUSAL_INCREASE_RELATIONS else -1)
        # Set polarity accordingly based on the relation type and whether
        # the object is a degradation node
        if deg_polarity * rel_polarity > 0:
            stmt_class = IncreaseAmount
        else:
            stmt_class = DecreaseAmount
        stmt = stmt_class(subj_agent, obj_agent)
        self.statements.append(stmt)

    def _get_modification(self, u_data, v_data, edge_data):
        subj_agent = _get_agent(u_data, edge_data.get(pc.SUBJECT))
        mods, muts = _get_all_pmods(v_data, edge_data)
        v_data_no_mods = _remove_pmods(v_data)
        obj_agent = _get_agent(v_data_no_mods,edge_data.get(pc.OBJECT))
        if subj_agent is None or obj_agent is None:
            return
        for mod in mods:
            modclass = modtype_to_modclass[mod.mod_type]
            ev = _get_evidence(edge_data)
            stmt = modclass(subj_agent, obj_agent, mod.residue, mod.position,
                            evidence=[ev])
            self.statements.append(stmt)

    def _get_regulate_activity(self, u_data, v_data, edge_data):
        subj_agent = _get_agent(u_data, edge_data.get(pc.SUBJECT))
        obj_agent = _get_agent(v_data)
        obj_activity_condition = \
                            _get_activity_condition(edge_data.get(pc.OBJECT))
        activity_type = obj_activity_condition.activity_type
        assert obj_activity_condition.is_active is True
        if subj_agent is None or obj_agent is None:
            return
        if edge_data[pc.RELATION] in pc.CAUSAL_INCREASE_RELATIONS:
            stmt_class = Activation
        else:
            stmt_class = Inhibition
        stmt = stmt_class(subj_agent, obj_agent, activity_type)
        self.statements.append(stmt)

    def _get_active_form(self, u_data, v_data, edge_data):
        subj_agent = _get_agent(u_data)
        obj_agent = _get_agent(v_data)
        if subj_agent is None or obj_agent is None:
            return
        obj_activity_condition = \
                            _get_activity_condition(edge_data.get(pc.OBJECT))
        activity_type = obj_activity_condition.activity_type
        # If the relation is DECREASES, this means that this agent state
        # is inactivating
        is_active = edge_data[pc.RELATION] in pc.CAUSAL_INCREASE_RELATIONS
        stmt = ActiveForm(subj_agent, activity_type, is_active)
        self.statements.append(stmt)

def _get_agent(node_data, node_modifier_data=None):
    # Check the node type/function
    node_func = node_data[pc.FUNCTION]
    if node_func not in (pc.PROTEIN, pc.RNA):
        logger.info("Nodes of type %s not handled", node_func)
        return None
    # Get node identifier information
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
                logger.info("Invalid HGNC name: %s (%s)" % (name, node_data))
                return None
            db_refs = {'HGNC': hgnc_id}
            up_id = _get_up_id(hgnc_id)
            if up_id:
                db_refs['UP'] = up_id
    # We've already got an identifier, look up other identifiers if necessary
    else:
        # Get the name, overwriting existing name if necessary
        if ns == 'HGNC':
            name = hgnc_client.get_hgnc_name(ident)
            db_refs = {'HGNC': ident}
            up_id = _get_up_id(ident)
            if up_id:
                db_refs['UP'] = up_id
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
        logger.info('Unable to get identifier information for node: %s'
                     % node_data)
        return None
    # Get modification conditions
    mods, muts = _get_all_pmods(node_data)
    # Get activity condition
    ac = _get_activity_condition(node_modifier_data)
    ag = Agent(name, db_refs=db_refs, mods=mods, activity=ac)
    return ag


def _get_evidence(edge_data):
    # TODO: @cthoyt put in some additional epistemics info from pybel
    # TODO: Also add additional provenance information from the bel/pybel
    # source document into annotations
    ev_text = edge_data.get(pc.EVIDENCE)
    ev_citation = edge_data.get(pc.CITATION)
    ev_pmid = None
    if ev_citation:
        cit_type = ev_citation[pc.CITATION_TYPE]
        cit_ref = ev_citation[pc.CITATION_REFERENCE]
        if cit_type == pc.CITATION_TYPE_PUBMED:
            ev_pmid = cit_ref
        else:
            ev_pmid = '%s: %s' % (cit_type, cit_ref)
    epistemics = {'direct': _rel_is_direct(edge_data)}
    annotations = edge_data.get(pc.ANNOTATIONS, {})
    ev = Evidence(text=ev_text, pmid=ev_pmid, source_api='pybel',
                  source_id=edge_data.get(pc.HASH), epistemics=epistemics,
                  annotations=annotations)
    return ev


def _rel_is_direct(d):
    return d[pc.RELATION] in (pc.DIRECTLY_INCREASES, pc.DIRECTLY_DECREASES)


def _get_up_id(hgnc_id):
    up_id = hgnc_client.get_uniprot_id(hgnc_id)
    if not up_id:
        logger.info("No Uniprot ID for HGNC ID %s" % hgnc_id)
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


def _remove_pmods(node_data):
    node_data_no_pmods = copy(node_data)
    variants = node_data.get(pc.VARIANTS)
    if variants:
        node_data_no_pmods[pc.VARIANTS] = [var for var in variants
                                               if var[pc.KIND] != pc.PMOD]
    return node_data_no_pmods


def _get_all_pmods(node_data, remove_pmods=False):
    mods = []
    muts = []
    variants = node_data.get(pc.VARIANTS)
    if not variants:
        return mods, muts

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
        # FIXME These unhandled mod types should result in throwing out
        # the node (raise, or return None)
        elif var[pc.KIND] == pc.GMOD:
            logger.debug('Unhandled node variant GMOD: %s' % node_data)
        elif var[pc.KIND] == pc.FRAG:
            logger.debug('Unhandled node variant FRAG: %s' % node_data)
        else:
            logger.debug('Unknown node variant type: %s' % node_data)
    return (mods, muts)


def _get_activity_condition(node_modifier_data):
    if node_modifier_data is None or node_modifier_data == {}:
        return None
    if node_modifier_data[pc.MODIFIER] != pc.ACTIVITY:
        return None
    effect = node_modifier_data.get(pc.EFFECT)
    # No specific effect, just return generic activity
    if not effect:
        return ActivityCondition('activity', True)

    activity_ns = effect[pc.NAMESPACE]
    if activity_ns == pc.BEL_DEFAULT_NAMESPACE:
        activity_name = effect[pc.NAME]
        activity_type = _pybel_indra_act_map.get(activity_name)
        # If an activity type in Bel/PyBel that is not implemented in INDRA,
        # return generic activity
        if activity_type is None:
            return ActivityCondition('activity', True)
        return ActivityCondition(activity_type, True)
    # If an unsupported namespace, simply return generic activity
    return ActivityCondition('activity', True)


def _proteins_match(u_data, v_data):
    return (
        u_data[pc.FUNCTION] == pc.PROTEIN and
        v_data[pc.FUNCTION] == pc.PROTEIN and
        pc.NAMESPACE in u_data and pc.NAMESPACE in v_data and
        pc.NAME in u_data and pc.NAME in v_data and
        u_data[pc.NAMESPACE] == v_data[pc.NAMESPACE] and
        u_data[pc.NAME] == v_data[pc.NAME]
    )
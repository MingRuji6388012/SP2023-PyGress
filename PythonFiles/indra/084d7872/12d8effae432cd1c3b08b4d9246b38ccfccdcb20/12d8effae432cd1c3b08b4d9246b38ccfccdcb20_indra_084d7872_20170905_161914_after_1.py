from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str
from indra.statements import *
from indra.databases import hgnc_client
import logging
import pybel
import pybel.constants as pc
from copy import deepcopy
from pybel.parser.language import pmod_namespace
from pybel.parser.parse_bel import canonicalize_variant
from indra.assemblers.pysb_assembler import mod_acttype_map
# Python 2
try:
    basestring
# Python 3
except:
    basestring = str

logger = logging.getLogger('pybel_assembler')


_indra_pybel_act_map = {
    'kinase': 'kin',
    'phosphatase': 'phos',
    'catalytic': 'cat',
    'gtpbound': 'gtp',
    'transcription': 'tscript',
}


class PybelAssembler(object):
    def __init__(self, stmts=None):
        if stmts is None:
            self.statements = []
        else:
            self.statements = stmts

        self.model = None

    def make_model(self, **kwargs):
        self.model = pybel.BELGraph(**kwargs)
        for stmt in self.statements:
            # Convert phosphorylation statements into
            # kin(p(agent)) => pmod(p(agent))
            if isinstance(stmt, Modification):
                self._assemble_modification(stmt)
            elif isinstance(stmt, RegulateActivity):
                self._assemble_regulate_activity(stmt)
            elif isinstance(stmt, RegulateAmount):
                self._assemble_regulate_amount(stmt)
        return self.model

    def _assemble_regulate_activity(self, stmt):
        # Get node data and add to model
        subj_node, subj_attr, subj_edge = _get_agent_node(stmt.subj)
        act_obj = _get_activated_object(stmt)
        obj_node, obj_attr, obj_edge = _get_agent_node(act_obj)
        self.model.add_node(subj_node, attr_dict=subj_attr)
        self.model.add_node(obj_node, attr_dict=obj_attr)
        # Define the edge data
        pybel_relation = pc.DIRECTLY_INCREASES \
                         if isinstance(stmt, Activation) \
                         else pc.DIRECTLY_DECREASES
        edge_data = _combine_edge_data(pybel_relation, subj_edge, obj_edge)
        self.model.add_edge(subj_node, obj_node, attr_dict=edge_data)

    def _assemble_modification(self, stmt):
        (enz_node, enz_attr, enz_edge) = _get_agent_node(stmt.enz)
        sub_agent = _get_modified_substrate(stmt)
        (sub_node, sub_attr, sub_edge) = _get_agent_node(sub_agent)
        self.model.add_node(enz_node, attr_dict=enz_attr)
        self.model.add_node(sub_node, attr_dict=sub_attr)
        pybel_relation = pc.DIRECTLY_INCREASES \
                         if isinstance(stmt, AddModification) \
                         else pc.DIRECTLY_DECREASES
        edge_data = _combine_edge_data(pybel_relation, enz_edge, sub_edge)
        self.model.add_edge(enz_node, sub_node, attr_dict=edge_data)

    def _assemble_regulate_amount(self, stmt):
        # p(HGNC:TP53) => p(HGNC:MDM2)
        (subj_node, subj_attr, subj_edge) = _get_agent_node(stmt.subj)
        (obj_node, obj_attr, obj_edge) = _get_agent_node(stmt.obj)
        self.model.add_node(subj_node, attr_dict=subj_attr)
        self.model.add_node(obj_node, attr_dict=obj_attr)
        pybel_relation = pc.DIRECTLY_INCREASES \
                         if isinstance(stmt, IncreaseAmount) \
                         else pc.DIRECTLY_DECREASES
        edge_data = _combine_edge_data(pybel_relation, subj_edge, obj_edge)
        self.model.add_edge(subj_node, obj_node, attr_dict=edge_data)


def _combine_edge_data(relation, subj_edge, obj_edge):
    edge_data = {pc.RELATION: relation}
    if subj_edge:
        edge_data[pc.SUBJECT] = subj_edge
    if obj_edge:
        edge_data[pc.OBJECT] = obj_edge
    return edge_data


def _get_modified_substrate(mod_stmt):
    mod_agent = deepcopy(mod_stmt.sub)
    mc = mod_stmt._get_mod_condition()
    mod_agent.mods.append(mc)
    return mod_agent


def _get_activated_object(reg_stmt):
    act_agent = deepcopy(reg_stmt.obj)
    ac = reg_stmt._get_activity_condition()
    act_agent.activity = ac
    return act_agent


def _get_agent_node(agent):
    (abundance_type, db_ns, db_id) = _get_agent_grounding(agent)
    if abundance_type is None:
        logging.warning('Agent %s has no grounding.', agent)
        return None
    node_attr = {pc.FUNCTION: abundance_type,
                 pc.NAMESPACE: db_ns,
                 pc.NAME: db_id}
    variants = []
    for mod in agent.mods:
        var = {pc.KIND: pc.PMOD,
               pc.IDENTIFIER: {
                   pc.NAMESPACE: pc.BEL_DEFAULT_NAMESPACE,
                   pc.NAME: pmod_namespace[mod.mod_type]}}
        if mod.residue is not None:
            res = amino_acids[mod.residue]['short_name'].capitalize()
            var[pc.PMOD_CODE] = res
        if mod.position is not None:
            var[pc.PMOD_POSITION] = int(mod.position)
        variants.append(var)
    for mut in agent.mutations:
        var = {pc.KIND: pc.HGVS,
               pc.IDENTIFIER: mut.to_hgvs()}
        variants.append(var)
    if variants:
        node_attr[pc.VARIANTS] = variants
    node_tuple = _make_node_tuple(node_attr)
    # Also get edge data for the agent
    edge_data = _get_agent_activity(agent)
    return (node_tuple, node_attr, edge_data)


def _get_agent_grounding(agent):
    hgnc_id = agent.db_refs.get('HGNC')
    uniprot_id = agent.db_refs.get('UP')
    be_id = agent.db_refs.get('BE')
    pfam_id = agent.db_refs.get('PF')
    fa_id = agent.db_refs.get('FA')
    chebi_id = agent.db_refs.get('CHEBI')
    pubchem_id = agent.db_refs.get('PUBCHEM')
    go_id = agent.db_refs.get('GO')
    mesh_id = agent.db_refs.get('MESH')
    if hgnc_id:
        hgnc_name = hgnc_client.get_hgnc_name(hgnc_id)
        return (pc.PROTEIN, 'HGNC', hgnc_name)
    elif up_id:
        return (pc.PROTEIN, 'UP', uniprot_id)
    elif be_id:
        return (pc.PROTEIN, 'BE', be_id)
    elif pfam_id:
        return (pc.PROTEIN, 'PFAM', be_id)
    elif fa_id:
        return (pc.PROTEIN, 'NXPFA', be_id)
    elif chebi_id:
        return (pc.ABUNDANCE, 'CHEBI', chebi_id)
    elif pubchem_id:
        return (pc.ABUNDANCE, 'PUBCHEM', pubchem_id)
    elif go_id:
        return (pc.BIOPROCESS, 'GO', go_id)
    elif mesh_id:
        return (pc.BIOPROCESS, 'MESH', mesh_id)
    else:
        return (None, None, None)


def _get_agent_activity(agent):
    ac = agent.activity
    if not ac:
        return None
    if not ac.is_active:
        raise ValueError('Cannot represent negative activity in PyBEL: %s' %
                         agent)
    edge_data = {pc.MODIFIER: pc.ACTIVITY}
    if not ac.activity_type == 'activity':
        pybel_activity = _indra_pybel_act_map[ac.activity_type]
        edge_data[pc.EFFECT] = {pc.NAME: pybel_activity,
                                pc.NAMESPACE: pc.BEL_DEFAULT_NAMESPACE}
    return edge_data


def _make_node_tuple(node_attr):
    if pc.VARIANTS in node_attr:
        variants = tuple(sorted([canonicalize_variant(token)
                                 for token in node_attr[pc.VARIANTS]]))
        return _make_simple_tuple(node_attr) + variants
    return _make_simple_tuple(node_attr)


def _make_simple_tuple(node_attr):
    return (node_attr[pc.FUNCTION], node_attr[pc.NAMESPACE], node_attr[pc.NAME])


def _get_evidence(stmt):
    # If there's no evidence for this statement, add node without
    # any evidence info
    if not stmt.evidence:
        edge_data[pc.ANNOTATIONS] = {}
        edge_data[pc.CITATION] = {}
        edge_data[pc.EVIDENCE] = ''
        self.model.add_edge(enz_node, sub_node,
                                 attr_dict=edge_data)
    # Otherwise, add an edge_data for each piece of evidence.
    else:
        for ev in stmt.evidence:
            edge_data[pc.ANNOTATIONS] = {}
            # FIXME Retrieve citation information from pubmed_client
            edge_data[pc.CITATION] = {'authors': '', 'comments': '',
                                 'date': '', 'name': '',
                                 'reference': ev.pmid,
                                 'type': 'PubMed'},
            edge_data[pc.EVIDENCE] = ev.text


def _get_evidence(evidence):
    pybel_ev = {pc.EVIDENCE: evidence.text}
    if evidence.pmid:
        citation = {pc.CITATION_TYPE: pc.CITATION_TYPE_PUBMED,
                    pc.CITATION_REFERENCE: evidence.pmid}
    else:
        citation = {}
    pybel_ev[pc.CITATION] = citation
    pybel_ev[pc.ANNOTATIONS] = {}
    return pybel_ev
>>>>>>> Generalize getting evidence

"""
Representation of PTM reactions in PyBEL/BEL
--------------------------------------------
- Kin -> pmod(Sub) vs.
- Kin -> rxn(Sub + ATP, pmod(Sub) + ADP)


structure of bel graph.
- node/tuple, maps to
  - dict with node/tuples as keys, each one mapped to
    - a dict, with integers (negative integers???) as keys, each one mapped to
      - a dict with edge information?

inner dict has fields such as
{'annotations': {},
'citation': {
    'authors': '',
    'comments': '',
    'date': '',
    'name': 'Mol Cell Biol 2001 Apr 21(8) 2659-70',
    'reference': '11283246',
    'type': 'PubMed'},
'evidence': 'Modified assertion',
'subject': {
    'effect': {'name': 'kin', 'namespace': 'bel'},
    'modifier': 'Activity'}}}
'relation': 'increases',
'object': {
    'effect': {'name': 'kin', 'namespace': 'bel'},
    'modifier': 'Activity'},

Note that Activity modifiers are listed in the subject/object dicts.

Edges are added between top level nodes and modified nodes using a hasVariant
relation:

('Protein',
  'HGNC',
  'BRAF',
  ('hgvs', 'p.Val600Glu')): {-4: {'relation': 'hasVariant'}},


"""

# Need function for building up terms from agent conditions, including
# (mainly for now) modification conditions

# Example nodes in graph:
"""
('Protein', 'RGD', 'Pdpk1', ('pmod', ('bel', 'Ph'))),
 ('Complex', ('Protein', 'HGNC', 'JUP'), ('Protein', 'PFH', 'AXIN Family')),
 ('RNA', 'HGNC', 'LTV1'),
 ('RNA', 'MGI', 'Nfix'),
 ('Protein', 'HGNC', 'PAX7'),
 ('RNA', 'HGNC', 'NEUROG1'),
 ('RNA', 'MGI', 'Mup1'),
 ('Protein', 'HGNC', 'PPARA'),
 ('RNA', 'EGID', '66935'),
 ('RNA', 'HGNC', 'AKIRIN1'),
"""

# Then need patterns for assembling modifications, activations, rasgef/gap

# Can start with this, then add evidence/context, etc.


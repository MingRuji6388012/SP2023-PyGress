import logging
from copy import deepcopy
from . import ModelChecker
from indra.statements import *
from indra.preassembler.hierarchy_manager import hierarchies
from .model_checker import signed_edges_to_signed_nodes

logger = logging.getLogger(__name__)


class PybelModelChecker(ModelChecker):
    """Check a PyBEL model against a set of INDRA statements.

    Parameters
    ----------
    model : pybel.BELGraph
        A Pybel model to check.
    statements : Optional[list[indra.statements.Statement]]
        A list of INDRA Statements to check the model against.
    do_sampling : bool
        Whether to use breadth-first search or weighted sampling to
        generate paths. Default is False (breadth-first search).
    seed : int
        Random seed for sampling (optional, default is None).
    """
    def __init__(self, model, statements=None, do_sampling=False, seed=None):
        super().__init__(model, statements, do_sampling, seed)
        self.model_agents = self._get_model_agents()

    def get_graph(self):
        """Convert a PyBELGraph to a graph with signed nodes."""
        # This import is done here rather than at the top level to avoid
        # making pybel an implicit dependency of the model checker
        from indra.assemblers.pybel.assembler import belgraph_to_signed_graph
        if self.graph:
            return self.graph
        signed_edges = belgraph_to_signed_graph(self.model)
        self.graph = signed_edges_to_signed_nodes(signed_edges)
        return self.graph

    def process_statement(self, stmt):
        # Check if this is one of the statement types that we can check
        if not isinstance(stmt, (Modification, RegulateAmount,
                                 RegulateActivity, Influence)):
            logger.info('Statement type %s not handled' %
                        stmt.__class__.__name__)
            return (None, None, 'STATEMENT_TYPE_NOT_HANDLED')
        subj, obj = stmt.agent_list()
        # Get the polarity for the statement
        if isinstance(stmt, Modification):
            target_polarity = 1 if isinstance(stmt, RemoveModification) else 0
            obj_agent = deepcopy(obj)
            obj_agent.mods.append(stmt._get_mod_condition())
            obj = obj_agent
        elif isinstance(stmt, RegulateActivity):
            target_polarity = 0 if stmt.is_activation else 1
            obj_agent = deepcopy(obj)
            obj_agent.activity = stmt._get_activity_condition()
            obj_agent.activity.is_active = True
            obj = obj_agent
        elif isinstance(stmt, RegulateAmount):
            target_polarity = 1 if isinstance(stmt, DecreaseAmount) else 0
        elif isinstance(stmt, Influence):
            target_polarity = 1 if stmt.overall_polarity() == -1 else 0
        subj_nodes = self.get_nodes(subj, self.graph, 0)
        if not subj_nodes:
            return (None, None, 'SUBJECT_NOT_FOUND')
        obj_nodes = self.get_nodes(obj, self.graph, target_polarity)
        if not obj_nodes:
            return (None, None, 'OBJECT_NOT_FOUND')
        return (subj_nodes, obj_nodes, None)

    def process_subject(self, subj):
        return [subj], None

    def get_nodes(self, agent, graph, target_polarity):
        # This import is done here rather than at the top level to avoid
        # making pybel an implicit dependency of the model checker
        from indra.assemblers.pybel.assembler import _get_agent_node
        nodes = set()
        if agent is None:
            return nodes
        # First get exact match
        agent_node = _get_agent_node(agent)[0]
        if agent_node:
            node = (agent_node, target_polarity)
            if node in graph.nodes:
                nodes.add(node)
        # Try get refined versions
        for ag in self.model_agents:
            if ag.refinement_of(agent, hierarchies):
                agent_node = _get_agent_node(ag)[0]
                if agent_node:
                    node = (agent_node, target_polarity)
                    if node in graph.nodes:
                        nodes.add(node)
        return nodes

    def _get_model_agents(self):
        # This import is done here rather than at the top level to avoid
        # making pybel an implicit dependency of the model checker
        from indra.sources.bel.processor import get_agent
        return [get_agent(node) for node in self.model.nodes]
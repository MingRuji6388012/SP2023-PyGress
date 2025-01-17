import numbers
import logging
from copy import deepcopy
from collections import Counter

import scipy.stats
import kappy
import itertools
import numpy as np
import networkx as nx
from pysb import WILD, export, Observable, ComponentSet, Annotation
from pysb.core import as_complex_pattern, ComponentDuplicateNameError
from indra.explanation.reporting import stmt_from_rule, agent_from_obs
from indra.statements import *
from indra.assemblers.pysb import assembler as pa
from indra.assemblers.pysb.kappa_util import im_json_to_graph
from indra.statements.agent import default_ns_order

from . import ModelChecker, PathResult
from .model_checker import signed_edges_to_signed_nodes

logger = logging.getLogger(__name__)

try:
    import paths_graph as pg
    has_pg = True
except ImportError:
    pg = None
    has_pg = False
    logger.warning('PathsGraph is not available')


class PysbModelChecker(ModelChecker):
    """Check a PySB model against a set of INDRA statements.

    Parameters
    ----------
    model : pysb.Model
        A PySB model to check.
    statements : Optional[list[indra.statements.Statement]]
        A list of INDRA Statements to check the model against.
    agent_obs: Optional[list[indra.statements.Agent]]
        A list of INDRA Agents in a given state to be observed.
    do_sampling : bool
        Whether to use breadth-first search or weighted sampling to
        generate paths. Default is False (breadth-first search).
    seed : int
        Random seed for sampling (optional, default is None).
    model_stmts : list[indra.statements.Statement]
        A list of INDRA statements used to assemble PySB model.
    """

    def __init__(self, model, statements=None, agent_obs=None,
                 do_sampling=False, seed=None, model_stmts=None):
        super().__init__(model, statements, do_sampling, seed)
        if agent_obs:
            self.agent_obs = agent_obs
        else:
            self.agent_obs = []
        self.model_stmts = model_stmts if model_stmts else []
        # Influence map
        self._im = None
        # Map from statements to associated observables
        self.stmt_to_obs = {}
        # Map from agents to associated observables
        self.agent_to_obs = {}
        # Map between rules and downstream observables
        self.rule_obs_dict = {}

    def generate_im(self, model):
        """Return a graph representing the influence map generated by Kappa

        Parameters
        ----------
        model : pysb.Model
            The PySB model whose influence map is to be generated

        Returns
        -------
        graph : networkx.MultiDiGraph
            A MultiDiGraph representing the influence map
        """
        kappa = kappy.KappaStd()
        model_str = export.export(model, 'kappa')
        kappa.add_model_string(model_str)
        kappa.project_parse()
        imap = kappa.analyses_influence_map(accuracy='medium')
        graph = im_json_to_graph(imap)
        return graph

    def draw_im(self, fname):
        """Draw and save the influence map in a file.

        Parameters
        ----------
        fname : str
            The name of the file to save the influence map in.
            The extension of the file will determine the file format,
            typically png or pdf.
        """
        im = self.get_im()
        im_agraph = nx.nx_agraph.to_agraph(im)
        im_agraph.draw(fname, prog='dot')

    def get_im(self, force_update=False):
        """Get the influence map for the model, generating it if necessary.

        Parameters
        ----------
        force_update : bool
            Whether to generate the influence map when the function is called.
            If False, returns the previously generated influence map if
            available. Defaults to True.

        Returns
        -------
        networkx MultiDiGraph object containing the influence map.
            The influence map can be rendered as a pdf using the dot layout
            program as follows::

                im_agraph = nx.nx_agraph.to_agraph(influence_map)
                im_agraph.draw('influence_map.pdf', prog='dot')
        """
        if self._im and not force_update:
            return self._im
        if not self.model:
            raise Exception("Cannot get influence map if there is no model.")

        def add_obs_for_agent(agent):
            obj_mps = list(pa.grounded_monomer_patterns(self.model, agent))
            if not obj_mps:
                logger.debug('No monomer patterns found in model for agent %s,'
                             ' skipping' % agent)
                return
            obs_list = []
            for obj_mp in obj_mps:
                obs_name = _monomer_pattern_label(obj_mp) + '_obs'
                # Add the observable
                obj_obs = Observable(obs_name, obj_mp, _export=False)
                obs_list.append(obs_name)
                try:
                    self.model.add_component(obj_obs)
                    self.model.add_annotation(
                        Annotation(obs_name, agent.name, 'from_indra_agent'))
                except ComponentDuplicateNameError as e:
                    pass
            return obs_list

        # Create observables for all statements to check, and add to model
        # Remove any existing observables in the model
        self.model.observables = ComponentSet([])
        for stmt in self.statements:
            # Generate observables for Modification statements
            if isinstance(stmt, Modification):
                if stmt.sub is None:
                    self.stmt_to_obs[stmt] = [None]
                else:
                    mod_condition_name = modclass_to_modtype[stmt.__class__]
                    if isinstance(stmt, RemoveModification):
                        mod_condition_name = modtype_to_inverse[
                            mod_condition_name]
                    # Add modification to substrate agent
                    modified_sub = _add_modification_to_agent(
                        stmt.sub, mod_condition_name, stmt.residue,
                        stmt.position)
                    obs_list = add_obs_for_agent(modified_sub)
                    # Associate this statement with this observable
                    self.stmt_to_obs[stmt] = obs_list
            # Generate observables for Activation/Inhibition statements
            elif isinstance(stmt, RegulateActivity):
                if stmt.obj is None:
                    self.stmt_to_obs[stmt] = [None]
                else:
                    regulated_obj, polarity = \
                            _add_activity_to_agent(stmt.obj, stmt.obj_activity,
                                                   stmt.is_activation)
                    obs_list = add_obs_for_agent(regulated_obj)
                    # Associate this statement with this observable
                    self.stmt_to_obs[stmt] = obs_list
            elif isinstance(stmt, RegulateAmount):
                if stmt.obj is None:
                    self.stmt_to_obs[stmt] = [None]
                else:
                    obs_list = add_obs_for_agent(stmt.obj)
                    self.stmt_to_obs[stmt] = obs_list
            elif isinstance(stmt, Influence):
                if stmt.obj is None:
                    self.stmt_to_obs[stmt] = [None]
                else:
                    obs_list = add_obs_for_agent(stmt.obj.concept)
                    self.stmt_to_obs[stmt] = obs_list
        # Add observables for each agent
        for ag in self.agent_obs:
            obs_list = add_obs_for_agent(ag)
            self.agent_to_obs[ag] = obs_list

        logger.info("Generating influence map")
        self._im = self.generate_im(self.model)
        # self._im.is_multigraph = lambda: False
        # Now, for every rule in the model, check if there are any observables
        # downstream; alternatively, for every observable in the model, get a
        # list of rules.
        # We'll need the dictionary to check if nodes are observables
        node_attributes = nx.get_node_attributes(self._im, 'node_type')
        for rule in self.model.rules:
            obs_list = []
            # Get successors of the rule node
            for neighb in self._im.neighbors(rule.name):
                # Check if the node is an observable
                if node_attributes[neighb] != 'variable':
                    continue
                # Get the edge and check the polarity
                edge_sign = _get_edge_sign(self._im, (rule.name, neighb))
                obs_list.append((neighb, edge_sign))
            self.rule_obs_dict[rule.name] = obs_list
        return self._im

    def get_graph(self, prune_im=True, prune_im_degrade=True,
                  prune_im_subj_obj=False, add_namespaces=False):
        """Get influence map and convert it to a graph with signed nodes."""
        if self.graph:
            return self.graph
        im = self.get_im(force_update=True)
        self.update_nodes_to_agents(self.model_stmts, add_namespaces)
        if prune_im:
            self.prune_influence_map()
        if prune_im_degrade:
            self.prune_influence_map_degrade_bind_positive(self.model_stmts)
        if prune_im_subj_obj:
            self.prune_influence_map_subj_obj()
        self.graph = signed_edges_to_signed_nodes(
            im, prune_nodes=False, edge_signs={'pos': 1, 'neg': -1})
        return self.graph

    def update_nodes_to_agents(self, model_stmts, add_namespaces=False):
        """Update influence map nodes to agents mapping, optionally add
        namespaces to influence map.
        """
        im = self.get_im()
        for node, data in im.nodes(data=True):
            ag = None
            # Node is observable
            if node.endswith('obs'):
                ag = agent_from_obs(node, self.model)
            # Node is rule
            else:
                stmt = stmt_from_rule(node, self.model, model_stmts)
                if stmt:
                    agents = [ag for ag in stmt.agent_list() if ag is not None]
                    if agents:
                        ag = agents[0]
            if ag:
                self.nodes_to_agents[node] = ag
                if add_namespaces:
                    ns_order = default_ns_order + ['PUBCHEM', 'TEXT']
                    ns = ag.get_grounding(ns_order)[0]
                    data['ns'] = ns
            else:
                logger.warning('Could not get agent for %s' % node)

    def process_statement(self, stmt):
        self.get_im()
        # Check if this is one of the statement types that we can check
        if not isinstance(stmt, (Modification, RegulateAmount,
                                 RegulateActivity, Influence)):
            logger.info('Statement type %s not handled' %
                        stmt.__class__.__name__)
            return (None, None, 'STATEMENT_TYPE_NOT_HANDLED')
        # Get the polarity for the statement
        if isinstance(stmt, Modification):
            target_polarity = 1 if isinstance(stmt, RemoveModification) else 0
        elif isinstance(stmt, RegulateActivity):
            target_polarity = 0 if stmt.is_activation else 1
        elif isinstance(stmt, RegulateAmount):
            target_polarity = 1 if isinstance(stmt, DecreaseAmount) else 0
        elif isinstance(stmt, Influence):
            target_polarity = 1 if stmt.overall_polarity() == -1 else 0
        # Get the subject and object (works also for Modifications)
        subj, obj = stmt.agent_list()
        # Get a list of monomer patterns matching the subject FIXME Currently
        # this will match rules with the corresponding monomer pattern on it.
        # In future, this statement should (possibly) also match rules in which
        # 1) the agent is in its active form, or 2) the agent is tagged as the
        # enzyme in a rule of the appropriate activity (e.g., a phosphorylation
        # rule) FIXME
        if subj is not None:
            subj_mps = list(pa.grounded_monomer_patterns(
                self.model, subj, ignore_activities=True))
            if not subj_mps:
                return (None, None, 'SUBJECT_MONOMERS_NOT_FOUND')
        else:
            subj_mps = [None]
        # Observables may not be found for an activation since there may be no
        # rule in the model activating the object, and the object may not have
        # an "active" site of the appropriate type
        obs_names = self.stmt_to_obs[stmt]
        if not obs_names:
            logger.info("No observables for stmt %s, returning False" % stmt)
            return (None, None, 'OBSERVABLES_NOT_FOUND')
        # Statement object is None
        if all(obs is None for obs in obs_names):
            # Cannot check modifications in this case
            if isinstance(stmt, Modification):
                return (None, None, 'STATEMENT_TYPE_NOT_HANDLED')
            obs_signed = [None]
        else:
            obs_signed = [(obs, target_polarity) for obs in obs_names]
        result_code = None
        return subj_mps, obs_signed, result_code

    def process_subject(self, subj_mp):
        if subj_mp is None:
            input_set_signed = None
        else:
            input_rule_set = self._get_input_rules(subj_mp)
            if not input_rule_set:
                logger.info('Input rules not found for %s' % subj_mp)
                return (None, 'INPUT_RULES_NOT_FOUND')
            input_set_signed = {(rule, 0) for rule in input_rule_set}
        return input_set_signed, None

    def _get_input_rules(self, subj_mp):
        if subj_mp is None:
            raise ValueError("Cannot take None as an argument for subj_mp.")
        input_rules = _match_lhs(subj_mp, self.model.rules)
        logger.debug('Found %s input rules matching %s' %
                     (len(input_rules), str(subj_mp)))
        # Filter to include only rules where the subj_mp is actually the
        # subject (i.e., don't pick up upstream rules where the subject
        # is itself a substrate/object)
        # FIXME: Note that this will eliminate rules where the subject
        # being checked is included on the left hand side as
        # a bound condition rather than as an enzyme.
        subj_rules = pa.rules_with_annotation(self.model,
                                              subj_mp.monomer.name,
                                              'rule_has_subject')
        logger.debug('%d rules with %s as subject' %
                     (len(subj_rules), subj_mp.monomer.name))
        input_rule_set = set([r.name for r in input_rules]).intersection(
                             set([r.name for r in subj_rules]))
        logger.debug('Final input rule set contains %d rules' %
                     len(input_rule_set))
        return input_rule_set

    def _sample_paths(self, input_rule_set, obs_name, target_polarity,
                      max_paths=1, max_path_length=5):
        if max_paths == 0:
            raise ValueError("max_paths cannot be 0 for path sampling.")
        if not has_pg:
            raise ImportError("Paths Graph is not imported")
        # Convert path polarity representation from 0/1 to 1/-1

        def convert_polarities(path_list):
            return [tuple((n[0], 0 if n[1] > 0 else 1) for n in path)
                    for path in path_list]

        pg_polarity = 0 if target_polarity > 0 else 1
        nx_graph = self._im_to_signed_digraph(self.get_im())
        # Add edges from dummy node to input rules
        source_node = 'SOURCE_NODE'
        for rule in input_rule_set:
            nx_graph.add_edge(source_node, rule, sign=0)
        # -------------------------------------------------
        # Create combined paths_graph
        f_level, b_level = pg.get_reachable_sets(nx_graph, source_node,
                                                 obs_name, max_path_length,
                                                 signed=True)
        pg_list = []
        for path_length in range(1, max_path_length+1):
            cfpg = pg.CFPG.from_graph(
                    nx_graph, source_node, obs_name, path_length, f_level,
                    b_level, signed=True, target_polarity=pg_polarity)
            pg_list.append(cfpg)
        combined_pg = pg.CombinedCFPG(pg_list)
        # Make sure the combined paths graph is not empty
        if not combined_pg.graph:
            pr = PathResult(
                False, 'NO_PATHS_FOUND', max_paths, max_path_length)
            pr.path_metrics = None
            pr.paths = []
            return pr

        # Get a dict of rule objects
        rule_obj_dict = {}
        for ann in self.model.annotations:
            if ann.predicate == 'rule_has_object':
                rule_obj_dict[ann.subject] = ann.object

        # Get monomer initial conditions
        ic_dict = {}
        for mon in self.model.monomers:
            # FIXME: A hack that depends on the _0 convention
            ic_name = '%s_0' % mon.name
            # TODO: Wrap this in try/except?
            ic_param = self.model.parameters[ic_name]
            ic_value = ic_param.value
            ic_dict[mon.name] = ic_value

        # Set weights in PG based on model initial conditions
        for cur_node in combined_pg.graph.nodes():
            edge_weights = {}
            rule_obj_list = []
            edge_weights_by_gene = {}
            for u, v in combined_pg.graph.out_edges(cur_node):
                v_rule = v[1][0]
                # Get the object of the rule (a monomer name)
                rule_obj = rule_obj_dict.get(v_rule)
                if rule_obj:
                    # Add to list so we can count instances by gene
                    rule_obj_list.append(rule_obj)
                    # Get the abundance of rule object from the initial
                    # conditions
                    # TODO: Wrap in try/except?
                    ic_value = ic_dict[rule_obj]
                else:
                    ic_value = 1.0
                edge_weights[(u, v)] = ic_value
                edge_weights_by_gene[rule_obj] = ic_value
            # Get frequency of different rule objects
            rule_obj_ctr = Counter(rule_obj_list)
            # Normalize results by weight sum and gene frequency at this level
            edge_weight_sum = sum(edge_weights_by_gene.values())
            edge_weights_norm = {}
            for e, v in edge_weights.items():
                v_rule = e[1][1][0]
                rule_obj = rule_obj_dict.get(v_rule)
                if rule_obj:
                    rule_obj_count = rule_obj_ctr[rule_obj]
                else:
                    rule_obj_count = 1
                edge_weights_norm[e] = ((v / float(edge_weight_sum)) /
                                        float(rule_obj_count))
            # Add edge weights to paths graph
            nx.set_edge_attributes(combined_pg.graph, name='weight',
                                   values=edge_weights_norm)

        # Sample from the combined CFPG
        paths = combined_pg.sample_paths(max_paths)
        # -------------------------------------------------
        if paths:
            pr = PathResult(True, 'PATHS_FOUND', max_paths, max_path_length)
            pr.path_metrics = None
            # Convert path polarity representation from 0/1 to 1/-1
            pr.paths = convert_polarities(paths)
            # Strip off the SOURCE_NODE prefix
            pr.paths = [p[1:] for p in pr.paths]
        else:
            assert False
            pr = PathResult(
                False, 'NO_PATHS_FOUND', max_paths, max_path_length)
            pr.path_metrics = None
            pr.paths = []
        return pr

    def score_paths(self, paths, agents_values, loss_of_function=False,
                    sigma=0.15, include_final_node=False):
        """Return scores associated with a given set of paths.

        Parameters
        ----------
        paths : list[list[tuple[str, int]]]
            A list of paths obtained from path finding. Each path is a list
            of tuples (which are edges in the path), with the first element
            of the tuple the name of a rule, and the second element its
            polarity in the path.
        agents_values : dict[indra.statements.Agent, float]
            A dictionary of INDRA Agents and their corresponding measured
            value in a given experimental condition.
        loss_of_function : Optional[boolean]
            If True, flip the polarity of the path. For instance, if the effect
            of an inhibitory drug is explained, set this to True.
            Default: False
        sigma : Optional[float]
            The estimated standard deviation for the normally distributed
            measurement error in the observation model used to score paths
            with respect to data. Default: 0.15
        include_final_node : Optional[boolean]
            Determines whether the final node of the path is included in the
            score. Default: False
        """
        obs_model = lambda x: scipy.stats.norm(x, sigma)
        # Build up dict mapping observables to values
        obs_dict = {}
        for ag, val in agents_values.items():
            obs_list = self.agent_to_obs[ag]
            if obs_list is not None:
                for obs in obs_list:
                    obs_dict[obs] = val
        # For every path...
        path_scores = []
        for path in paths:
            logger.info('------')
            logger.info("Scoring path:")
            logger.info(path)
            # Look at every node in the path, excluding the final
            # observable...
            path_score = 0
            last_path_node_index = -1 if include_final_node else -2
            for node, sign in path[:last_path_node_index]:
                # ...and for each node check the sign to see if it matches the
                # data. So the first thing is to look at what's downstream
                # of the rule
                # affected_obs is a list of observable names alogn
                for affected_obs, rule_obs_sign in self.rule_obs_dict[node]:
                    flip_polarity = -1 if loss_of_function else 1
                    pred_sign = sign * rule_obs_sign * flip_polarity
                    # Check to see if this observable is in the data
                    logger.info('%s %s: effect %s %s' %
                                (node, sign, affected_obs, pred_sign))
                    measured_val = obs_dict.get(affected_obs)
                    if measured_val:
                        # For negative predictions use CDF (prob that given
                        # measured value, true value lies below 0)
                        if pred_sign <= 0:
                            prob_correct = obs_model(measured_val).logcdf(0)
                        # For positive predictions, use log survival function
                        # (SF = 1 - CDF, i.e., prob that true value is
                        # above 0)
                        else:
                            prob_correct = obs_model(measured_val).logsf(0)
                        logger.info('Actual: %s, Log Probability: %s' %
                                    (measured_val, prob_correct))
                        path_score += prob_correct
                if not self.rule_obs_dict[node]:
                    logger.info('%s %s' % (node, sign))
                    prob_correct = obs_model(0).logcdf(0)
                    logger.info('Unmeasured node, Log Probability: %s' %
                                (prob_correct))
                    path_score += prob_correct
            # Normalized path
            # path_score = path_score / len(path)
            logger.info("Path score: %s" % path_score)
            path_scores.append(path_score)
        path_tuples = list(zip(paths, path_scores))
        # Sort first by path length
        sorted_by_length = sorted(path_tuples, key=lambda x: len(x[0]))
        # Sort by probability; sort in reverse order to large values
        # (higher probabilities) are ranked higher
        scored_paths = sorted(sorted_by_length, key=lambda x: x[1],
                              reverse=True)
        return scored_paths

    def prune_influence_map(self):
        """Remove edges between rules causing problematic non-transitivity.

        First, all self-loops are removed. After this initial step, edges are
        removed between rules when they share *all* child nodes except for each
        other; that is, they have a mutual relationship with each other and
        share all of the same children.

        Note that edges must be removed in batch at the end to prevent edge
        removal from affecting the lists of rule children during the comparison
        process.
        """
        im = self.get_im()

        # First, remove all self-loops
        logger.info('Removing self loops')
        edges_to_remove = []
        for e in im.edges():
            if e[0] == e[1]:
                logger.info('Removing self loop: %s', e)
                edges_to_remove.append((e[0], e[1]))
        # Now remove all the edges to be removed with a single call
        im.remove_edges_from(edges_to_remove)

        # Remove parameter nodes from influence map
        remove_im_params(self.model, im)

        # Now compare nodes pairwise and look for overlap between child nodes
        logger.info('Get successors of each node')
        succ_dict = {}
        for node in im.nodes():
            succ_dict[node] = set(im.successors(node))
        # Sort and then group nodes by number of successors
        logger.info('Compare combinations of successors')
        group_key_fun = lambda x: len(succ_dict[x])
        nodes_sorted = sorted(im.nodes(), key=group_key_fun)
        groups = itertools.groupby(nodes_sorted, key=group_key_fun)
        # Now iterate over each group and then construct combinations
        # within the group to check for shared sucessors
        edges_to_remove = []
        for gix, group in groups:
            combos = itertools.combinations(group, 2)
            for ix, (p1, p2) in enumerate(combos):
                # Children are identical except for mutual relationship
                if succ_dict[p1].difference(succ_dict[p2]) == set([p2]) and \
                   succ_dict[p2].difference(succ_dict[p1]) == set([p1]):
                    for u, v in ((p1, p2), (p2, p1)):
                        edges_to_remove.append((u, v))
                        logger.debug('Will remove edge (%s, %s)', u, v)
        logger.info('Removing %d edges from influence map' %
                    len(edges_to_remove))
        # Now remove all the edges to be removed with a single call
        im.remove_edges_from(edges_to_remove)

    def prune_influence_map_subj_obj(self):
        """Prune influence map to include only edges where the object of the
        upstream rule matches the subject of the downstream rule."""
        def get_rule_info(r):
            result = {}
            for ann in self.model.annotations:
                if ann.subject == r:
                    if ann.predicate == 'rule_has_subject':
                        result['subject'] = ann.object
                    elif ann.predicate == 'rule_has_object':
                        result['object'] = ann.object
            return result
        im = self.get_im()
        rules = im.nodes()
        edges_to_prune = []
        for r1, r2 in itertools.permutations(rules, 2):
            if (r1, r2) not in im.edges():
                continue
            r1_info = get_rule_info(r1)
            r2_info = get_rule_info(r2)
            if 'object' not in r1_info or 'subject' not in r2_info:
                continue
            if r1_info['object'] != r2_info['subject']:
                logger.info("Removing edge %s --> %s" % (r1, r2))
                edges_to_prune.append((r1, r2))
        logger.info('Removing %d edges from influence map' %
                    len(edges_to_prune))
        im.remove_edges_from(edges_to_prune)

    def prune_influence_map_degrade_bind_positive(self, model_stmts):
        """Prune positive edges between X degrading and X forming a
        complex with Y."""
        im = self.get_im()
        edges_to_prune = []
        for r1, r2, data in im.edges(data=True):
            s1 = stmt_from_rule(r1, self.model, model_stmts)
            s2 = stmt_from_rule(r2, self.model, model_stmts)
            # Make sure this is a degradation/binding combo
            s1_is_degrad = (s1 and isinstance(s1, DecreaseAmount))
            s2_is_bind = (s2 and isinstance(s2, Complex) and 'bind' in r2)
            if not s1_is_degrad or not s2_is_bind:
                continue
            # Make sure what is degraded is part of the complex
            if s1.obj.name not in [m.name for m in s2.members]:
                continue
            # Make sure we're dealing with a positive influence
            if data['sign'] == 1:
                edges_to_prune.append((r1, r2))
        logger.info('Removing %d edges from influence map' %
                    len(edges_to_prune))
        im.remove_edges_from(edges_to_prune)

    def _im_to_signed_digraph(self, im):
        edges = []
        for e in im.edges():
            edge_sign = _get_edge_sign(im, e)
            polarity = 0 if edge_sign > 0 else 1
            edges.append((e[0], e[1], {'sign': polarity}))
        dg = nx.DiGraph()
        dg.add_edges_from(edges)
        return dg


def _find_sources_sample(im, target, sources, polarity, rule_obs_dict,
                         agent_to_obs, agents_values):
    # Build up dict mapping observables to values
    obs_dict = {}
    for ag, val in agents_values.items():
        obs_list = agent_to_obs[ag]
        for obs in obs_list:
            obs_dict[obs] = val

    sigma = 0.2

    def obs_model(x):
        return scipy.stats.norm(x, sigma)

    def _sample_pred(im, target, rule_obs_dict, obs_model):
        preds = list(_get_signed_predecessors(im, target, 1))
        if not preds:
            return None
        pred_scores = []
        for pred, sign in preds:
            pred_score = 0
            for affected_obs, rule_obs_sign in rule_obs_dict[pred]:
                pred_sign = sign * rule_obs_sign
                # Check to see if this observable is in the data
                logger.info('%s %s: effect %s %s' %
                            (pred, sign, affected_obs, pred_sign))
                measured_val = obs_dict.get(affected_obs)
                if measured_val:
                    logger.info('Actual: %s' % measured_val)
                    # The tail probability of the real value being above 1
                    tail_prob = obs_model(measured_val).cdf(1)
                    pred_score += (tail_prob if pred_sign == 1 else
                                   1-tail_prob)
            pred_scores.append(pred_score)
        # Normalize scores
        pred_scores = np.array(pred_scores) / np.sum(pred_scores)
        pred_idx = np.random.choice(range(len(preds)), p=pred_scores)
        pred = preds[pred_idx]
        return pred

    preds = []
    for i in range(100):
        pred = _sample_pred(im, target, rule_obs_dict, obs_model)
        preds.append(pred[0])


def remove_im_params(model, im):
    """Remove parameter nodes from the influence map.

    Parameters
    ----------
    model : pysb.core.Model
        PySB model.
    im : networkx.MultiDiGraph
        Influence map.

    Returns
    -------
    networkx.MultiDiGraph
        Influence map with the parameter nodes removed.
    """
    for param in model.parameters:
        # If the node doesn't exist e.g., it may have already been removed),
        # skip over the parameter without error
        try:
            im.remove_node(param.name)
        except:
            pass


def _get_signed_predecessors(im, node, polarity):
    """Get upstream nodes in the influence map.
    Return the upstream nodes along with the overall polarity of the path
    to that node by account for the polarity of the path to the given node
    and the polarity of the edge between the given node and its immediate
    predecessors.
    Parameters
    ----------
    im : networkx.MultiDiGraph
        Graph containing the influence map.
    node : str
        The node (rule name) in the influence map to get predecessors (upstream
        nodes) for.
    polarity : int
        Polarity of the overall path to the given node.
    Returns
    -------
    generator of tuples, (node, polarity)
        Each tuple returned contains two elements, a node (string) and the
        polarity of the overall path (int) to that node.
    """
    signed_pred_list = []
    for pred in im.predecessors(node):
        pred_edge = (pred, node)
        yield (pred, _get_edge_sign(im, pred_edge) * polarity)


def _get_edge_sign(im, edge):
    """Get the polarity of the influence by examining the edge sign."""
    edge_data = im[edge[0]][edge[1]]
    # Handle possible multiple edges between nodes
    signs = list(set([v['sign'] for v in edge_data.values()
                                  if v.get('sign')]))
    if len(signs) > 1:
        logger.warning("Edge %s has conflicting polarities; choosing "
                       "positive polarity by default" % str(edge))
        sign = 1
    else:
        sign = signs[0]
    if sign is None:
        raise Exception('No sign attribute for edge.')
    elif abs(sign) == 1:
        return sign
    else:
        raise Exception('Unexpected edge sign: %s' % edge.attr['sign'])


def _add_modification_to_agent(agent, mod_type, residue, position):
    """Add a modification condition to an Agent."""
    new_mod = ModCondition(mod_type, residue, position)
    # Check if this modification already exists
    for old_mod in agent.mods:
        if old_mod.equals(new_mod):
            return agent
    new_agent = deepcopy(agent)
    new_agent.mods.append(new_mod)
    return new_agent


def _add_activity_to_agent(agent, act_type, is_active):
    # Default to active, and return polarity if it's an inhibition
    new_act = ActivityCondition(act_type, True)
    # Check if this state already exists
    if agent.activity is not None and agent.activity.equals(new_act):
        return agent
    new_agent = deepcopy(agent)
    new_agent.activity = new_act
    polarity = 1 if is_active else -1
    return (new_agent, polarity)


def _match_lhs(cp, rules):
    """Get rules with a left-hand side matching the given ComplexPattern."""
    rule_matches = []
    for rule in rules:
        reactant_pattern = rule.rule_expression.reactant_pattern
        for rule_cp in reactant_pattern.complex_patterns:
            if _cp_embeds_into(rule_cp, cp):
                rule_matches.append(rule)
                break
    return rule_matches


def _cp_embeds_into(cp1, cp2):
    """Check that any state in ComplexPattern2 is matched in ComplexPattern1.
    """
    # Check that any state in cp2 is matched in cp1
    # If the thing we're matching to is just a monomer pattern, that makes
    # things easier--we just need to find the corresponding monomer pattern
    # in cp1
    if cp1 is None or cp2 is None:
        return False
    cp1 = as_complex_pattern(cp1)
    cp2 = as_complex_pattern(cp2)
    if len(cp2.monomer_patterns) == 1:
        mp2 = cp2.monomer_patterns[0]
        # Iterate over the monomer patterns in cp1 and see if there is one
        # that has the same name
        for mp1 in cp1.monomer_patterns:
            if _mp_embeds_into(mp1, mp2):
                return True
    return False


def _mp_embeds_into(mp1, mp2):
    """Check that conditions in MonomerPattern2 are met in MonomerPattern1."""
    sc_matches = []
    if mp1.monomer.name != mp2.monomer.name:
        return False
    # Check that all conditions in mp2 are met in mp1
    for site_name, site_state in mp2.site_conditions.items():
        if site_name not in mp1.site_conditions or \
           site_state != mp1.site_conditions[site_name]:
            return False
    return True


def _monomer_pattern_label(mp):
    """Return a string label for a MonomerPattern."""
    site_strs = []
    for site, cond in mp.site_conditions.items():
        if isinstance(cond, tuple) or isinstance(cond, list):
            assert len(cond) == 2
            if cond[1] == WILD:
                site_str = '%s_%s' % (site, cond[0])
            else:
                site_str = '%s_%s%s' % (site, cond[0], cond[1])
        elif isinstance(cond, numbers.Real):
            continue
        else:
            site_str = '%s_%s' % (site, cond)
        site_strs.append(site_str)
    return '%s_%s' % (mp.monomer.name, '_'.join(site_strs))

# -*- coding: utf-8 -*-
"""
This module takes the TEES parse graph generated by parse_tees and converts it
into INDRA statements.

See publication:
Jari Björne, Sofie Van Landeghem, Sampo Pyysalo, Tomoko Ohta, Filip Ginter,
Yves Van de Peer, Sofia Ananiadou and Tapio Salakoski, PubMed-Scale Event
Extraction for Post-Translational Modifications, Epigenetics and Protein
Structural Relations. Proceedings of BioNLP 2012, pages 82-90, 2012.
"""

from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str
from future.utils import python_2_unicode_compatible

import requests
from indra.statements import Phosphorylation, Dephosphorylation, Complex, \
        IncreaseAmount, DecreaseAmount, Agent, Evidence
from indra.sources.tees.parse_tees import parse_output
from indra.preassembler.grounding_mapper.gilda import ground_statements
from networkx.algorithms import dag
import os.path


class TEESProcessor(object):
    """Converts the output of the TEES reader to INDRA statements.

    Only extracts a subset of INDRA statements. Currently supported
    statements are:
    * Phosphorylation
    * Dephosphorylation
    * Binding
    * IncreaseAmount
    * DecreaseAmount

    Parameters
    ----------
    a1_text : str
        The TEES a1 output file, with entity information
    a2_text : str
        The TEES a2 output file, with the event graph
    sentence_segmentations : str
        The TEES sentence segmentation XML output
    pmid : int
        The pmid which the text comes from, or None if we don't want to specify
        at the moment. Stored in the Evidence object for each statement.

    Attributes
    ----------
    statements : list[indra.statements.Statement]
        A list of INDRA statements extracted from the provided text via TEES
    """

    def __init__(self, a1_text, a2_text, sentence_segmentations, pmid):
        # Store pmid
        self.pmid = pmid

        # Run TEES and parse into networkx graph
        self.G = parse_output(a1_text, a2_text, sentence_segmentations)

        # Extract statements from the TEES graph
        self.statements = []
        self.statements.extend(self.process_phosphorylation_statements())
        self.statements.extend(self.process_binding_statements())
        self.statements.extend(self.process_increase_expression_amount())
        self.statements.extend(self.process_decrease_expression_amount())

        # Ground statements
        ground_statements(self.statements)

    def node_has_edge_with_label(self, node_name, edge_label):
        """Looks for an edge from node_name to some other node with the specified
        label. Returns the node to which this edge points if it exists, or None
        if it doesn't.

        Parameters
        ----------
        G :
            The graph object
        node_name :
            Node that the edge starts at
        edge_label :
            The text in the relation property of the edge
        """
        G = self.G
        for edge in G.edges(node_name):
            to = edge[1]

            relation_name = G.edges[node_name, to]['relation']
            if relation_name == edge_label:
                return to
        return None

    def general_node_label(self, node):
        """Used for debugging - gives a short text description of a
        graph node."""
        G = self.G
        if G.node[node]['is_event']:
            return 'event type=' + G.node[node]['type']
        else:
            return 'entity text=' + G.node[node]['text']

    def print_parent_and_children_info(self, node):
        """Used for debugging - prints a short description of a a node, its
        children, its parents, and its parents' children."""
        G = self.G
        parents = G.predecessors(node)
        children = G.successors(node)

        print(general_node_label(G, node))
        tabs = '\t'
        for parent in parents:
            relation = G.edges[parent, node]['relation']
            print(tabs + 'Parent (%s): %s' % (relation,
                  general_node_label(G, parent)))
            for cop in G.successors(parent):
                if cop != node:
                    relation = G.edges[parent, cop]['relation']
                    print(tabs + 'Child of parent (%s): %s' % (relation,
                          general_node_label(G, cop)))
        for child in children:
            relation = G.edges[node, child]['relation']
            print(tabs + 'Child (%s): (%s)' % (relation,
                                               general_node_label(G, child)))

    def find_event_parent_with_event_child(self, parent_name, child_name):
        """Finds all event nodes (is_event node attribute is True) that are
        of the type parent_name, that have a child event node with the type
        child_name."""
        G = self.G
        matches = []
        for n in G.node.keys():
            if G.node[n]['is_event'] and G.node[n]['type'] == parent_name:
                children = G.successors(n)
                for child in children:
                    if G.node[child]['is_event'] and \
                            G.node[child]['type'] == child_name:
                        matches.append((n, child))
                        break
        return list(set(matches))

    def find_event_with_outgoing_edges(self, event_name, desired_relations):
        """Gets a list of event nodes with the specified event_name and
        outgoing edges annotated with each of the specified relations.

        Parameters
        ----------
        event_name : str
            Look for event nodes with this name
        desired_relations : list[str]
            Look for event nodes with outgoing edges annotated with each of
            these relations

        Returns
        -------
        event_nodes : list[str]
            Event nodes that fit the desired criteria
        """

        G = self.G
        desired_relations = set(desired_relations)

        desired_event_nodes = []

        for node in G.node.keys():
            if G.node[node]['is_event'] and G.node[node]['type'] == event_name:
                has_relations = [G.edges[node, edge[1]]['relation'] for
                                 edge in G.edges(node)]
                has_relations = set(has_relations)
                # Did the outgoing edges from this node have all of the
                # desired relations?
                if desired_relations.issubset(has_relations):
                    desired_event_nodes.append(node)
        return desired_event_nodes

    def get_related_node(self, node, relation):
        """Looks for an edge from node to some other node, such that the edge
        is annotated with the given relation. If there exists such an edge,
        returns the name of the node it points to. Otherwise, returns None."""
        G = self.G
        for edge in G.edges(node):
            to = edge[1]

            to_relation = G.edges[node, to]['relation']
            if to_relation == relation:
                return to
        return None

    def get_entity_text_for_relation(self, node, relation):
        """Looks for an edge from node to some other node, such that the edge is
        annotated with the given relation. If there exists such an edge, and
        the node at the other edge is an entity, return that entity's text.
        Otherwise, returns None."""

        G = self.G
        related_node = self.get_related_node(node, relation)
        if related_node is not None:
            if not G.node[related_node]['is_event']:
                return G.node[related_node]['text']
            else:
                return None
        else:
            return None

    def process_increase_expression_amount(self):
        """Looks for Positive_Regulation events with a specified Cause
        and a Gene_Expression theme, and processes them into INDRA statements.
        """
        statements = []

        pwcs = self.find_event_parent_with_event_child(
                'Positive_regulation', 'Gene_expression')
        for pair in pwcs:
            pos_reg = pair[0]
            expression = pair[1]

            cause = self.get_entity_text_for_relation(pos_reg, 'Cause')
            target = self.get_entity_text_for_relation(expression, 'Theme')

            if cause is not None and target is not None:
                theme_node = self.get_related_node(expression, 'Theme')
                assert(theme_node is not None)
                evidence = self.node_to_evidence(theme_node, is_direct=False)

                statements.append(IncreaseAmount(s2a(cause), s2a(target),
                                  evidence=evidence))
        return statements

    def process_decrease_expression_amount(self):
        """Looks for Negative_Regulation events with a specified Cause
        and a Gene_Expression theme, and processes them into INDRA statements.
        """
        statements = []

        pwcs = self.find_event_parent_with_event_child(
                'Negative_regulation', 'Gene_expression')
        for pair in pwcs:
            pos_reg = pair[0]
            expression = pair[1]

            cause = self.get_entity_text_for_relation(pos_reg, 'Cause')
            target = self.get_entity_text_for_relation(expression, 'Theme')

            if cause is not None and target is not None:
                theme_node = self.get_related_node(expression, 'Theme')
                assert(theme_node is not None)
                evidence = self.node_to_evidence(theme_node, is_direct=False)

                statements.append(DecreaseAmount(
                    s2a(cause), s2a(target), evidence=evidence))
        return statements

    def process_phosphorylation_statements(self):
        """Looks for Phosphorylation events in the graph and extracts them into
        INDRA statements.

        In particular, looks for a Positive_regulation event node with a child
        Phosphorylation event node.

        If Positive_regulation has an outgoing Cause edge, that's the subject
        If Phosphorylation has an outgoing Theme edge, that's the object
        If Phosphorylation has an outgoing Site edge, that's the site
        """
        G = self.G
        statements = []

        pwcs = self.find_event_parent_with_event_child('Positive_regulation',
                                                       'Phosphorylation')
        for pair in pwcs:
            (pos_reg, phos) = pair
            cause = self.get_entity_text_for_relation(pos_reg, 'Cause')
            theme = self.get_entity_text_for_relation(phos, 'Theme')
            print('Cause:', cause, 'Theme:', theme)

            # If the trigger word is dephosphorylate or similar, then we
            # extract a dephosphorylation statement
            trigger_word = self.get_entity_text_for_relation(phos,
                                                             'Phosphorylation')
            if 'dephos' in trigger_word:
                deph = True
            else:
                deph = False

            site = self.get_entity_text_for_relation(phos, 'Site')

            theme_node = self.get_related_node(phos, 'Theme')
            assert(theme_node is not None)
            evidence = self.node_to_evidence(theme_node, is_direct=False)

            if theme is not None:
                if deph:
                    statements.append(Dephosphorylation(s2a(cause),
                                      s2a(theme), site, evidence=evidence))
                else:
                    statements.append(Phosphorylation(s2a(cause),
                                      s2a(theme), site, evidence=evidence))
        return statements

    def process_binding_statements(self):
        """Looks for Binding events in the graph and extracts them into INDRA
        statements.

        In particular, looks for a Binding event node with outgoing edges
        with relations Theme and Theme2 - the entities these edges point to
        are the two constituents of the Complex INDRA statement.
        """
        G = self.G
        statements = []

        binding_nodes = self.find_event_with_outgoing_edges('Binding',
                                                            ['Theme',
                                                                'Theme2'])

        for node in binding_nodes:
            theme1 = self.get_entity_text_for_relation(node, 'Theme')
            theme1_node = self.get_related_node(node, 'Theme')
            theme2 = self.get_entity_text_for_relation(node, 'Theme2')

            assert(theme1 is not None)
            assert(theme2 is not None)

            evidence = self.node_to_evidence(theme1_node, is_direct=True)
            statements.append(Complex([s2a(theme1), s2a(theme2)],
                              evidence=evidence))

        return statements

    def node_to_evidence(self, entity_node, is_direct):
        """Computes an evidence object for a statement.

        We assume that the entire event happens within a single statement, and
        get the text of the sentence by getting the text of the sentence
        containing the provided node that corresponds to one of the entities
        participanting in the event.

        The Evidence's pmid is whatever was provided to the constructor
        (perhaps None), and the annotations are the subgraph containing the
        provided node, its ancestors, and its descendants.
        """

        # We assume that the entire event is within a single sentence, and
        # get this sentence by getting the sentence containing one of the
        # entities
        sentence_text = self.G.node[entity_node]['sentence_text']

        # Make annotations object containing the fully connected subgraph
        # containing these nodes
        subgraph = self.connected_subgraph(entity_node)
        edge_properties = {}
        for edge in subgraph.edges():
            edge_properties[edge] = subgraph.edges[edge]

        annotations = {'node_properties': subgraph.node,
                       'edge_properties': edge_properties}

        # Make evidence object
        epistemics = dict()
        evidence = Evidence(source_api='tees',
                            pmid=self.pmid,
                            text=sentence_text,
                            epistemics={'direct': is_direct},
                            annotations=annotations)
        return evidence

    def connected_subgraph(self, node):
        """Returns the subgraph containing the given node, its ancestors, and
        its descendants.

        Parameters
        ----------
        node : str
            We want to create the subgraph containing this node.

        Returns
        -------
        subgraph : networkx.DiGraph
            The subgraph containing the specified node.
        """
        G = self.G

        subgraph_nodes = set()
        subgraph_nodes.add(node)
        subgraph_nodes.update(dag.ancestors(G, node))
        subgraph_nodes.update(dag.descendants(G, node))

        # Keep adding the ancesotrs and descendants on nodes of the graph
        # until we can't do so any longer
        graph_changed = True
        while graph_changed:
            initial_count = len(subgraph_nodes)

            old_nodes = set(subgraph_nodes)
            for n in old_nodes:
                subgraph_nodes.update(dag.ancestors(G, n))
                subgraph_nodes.update(dag.descendants(G, n))

            current_count = len(subgraph_nodes)
            graph_changed = current_count > initial_count

        return G.subgraph(subgraph_nodes)


def s2a(s):
    """Makes an Agent from a string describing the agent."""
    return Agent(s, db_refs={'TEXT': s})

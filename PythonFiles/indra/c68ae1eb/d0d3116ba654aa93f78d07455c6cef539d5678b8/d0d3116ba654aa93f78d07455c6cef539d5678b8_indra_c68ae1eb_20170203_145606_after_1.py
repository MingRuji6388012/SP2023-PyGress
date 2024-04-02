from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str
import sys
import time
import logging
import itertools
import collections
from copy import copy, deepcopy
import numpy as np
from matplotlib import pyplot as plt
try:
    import pygraphviz as pgv
except ImportError:
    pass
from indra.statements import *
from indra.databases import uniprot_client

logger = logging.getLogger('preassembler')

from matplotlib import pyplot as plt
import numpy as np

class Preassembler(object):
    """De-duplicates statements and arranges them in a specificity hierarchy.

    Parameters
    ----------
    hierarchies : dict[:py:class:`indra.preassembler.hierarchy_manager`]
        A dictionary of hierarchies with keys such as 'entity' (hierarchy of
        entities, primarily specifying relationships between genes and their
        families) and 'modification' pointing to HierarchyManagers
    stmts : list of :py:class:`indra.statements.Statement` or None
        A set of statements to perform pre-assembly on. If None, statements
        should be added using the :py:meth:`add_statements` method.

    Attributes
    ----------
    stmts : list of :py:class:`indra.statements.Statement`
        Starting set of statements for preassembly.
    unique_stmts : list of :py:class:`indra.statements.Statement`
        Statements resulting from combining duplicates.
    related_stmts : list of :py:class:`indra.statements.Statement`
        Top-level statements after building the refinement hierarchy.
    hierarchies : dict[:py:class:`indra.preassembler.hierarchy_manager`]
        A dictionary of hierarchies with keys such as 'entity' and
        'modification' pointing to HierarchyManagers
    """
    def __init__(self, hierarchies, stmts=None):
        self.hierarchies = hierarchies
        if stmts:
            self.stmts = deepcopy(stmts)
        else:
            self.stmts = []
        self.unique_stmts = []
        self.related_stmts = []

    def add_statements(self, stmts):
        """Add to the current list of statements.

        Parameters
        ----------
        stmts : list of :py:class:`indra.statements.Statement`
            Statements to add to the current list.
        """
        self.stmts += deepcopy(stmts)

    def combine_duplicates(self):
        """Combine duplicates among `stmts` and save result in `unique_stmts`.

        A wrapper around the static method :py:meth:`combine_duplicate_stmts`.
        """
        self.unique_stmts = self.combine_duplicate_stmts(self.stmts)
        return self.unique_stmts

    @staticmethod
    def combine_duplicate_stmts(stmts):
        """Combine evidence from duplicate Statements.

        Statements are deemed to be duplicates if they have the same key
        returned by the `matches_key()` method of the Statement class. This
        generally means that statements must be identical in terms of their
        arguments and can differ only in their associated `Evidence` objects.

        This function keeps the first instance of each set of duplicate
        statements and merges the lists of Evidence from all of the other
        statements.

        Parameters
        ----------
        stmts : list of :py:class:`indra.statements.Statement`
            Set of statements to de-duplicate.

        Returns
        -------
        list of :py:class:`indra.statements.Statement`
            Unique statements with accumulated evidence across duplicates.

        Examples
        --------
        De-duplicate and combine evidence for two statements differing only
        in their evidence lists:

        >>> map2k1 = Agent('MAP2K1')
        >>> mapk1 = Agent('MAPK1')
        >>> stmt1 = Phosphorylation(map2k1, mapk1, 'T', '185',
        ... evidence=[Evidence(text='evidence 1')])
        >>> stmt2 = Phosphorylation(map2k1, mapk1, 'T', '185',
        ... evidence=[Evidence(text='evidence 2')])
        >>> uniq_stmts = Preassembler.combine_duplicate_stmts([stmt1, stmt2])
        >>> uniq_stmts
        [Phosphorylation(MAP2K1(), MAPK1(), T, 185)]
        >>> sorted([e.text for e in uniq_stmts[0].evidence]) # doctest:+IGNORE_UNICODE
        ['evidence 1', 'evidence 2']
        """
        unique_stmts = []
        # Remove exact duplicates using a set() call, then make copies:
        st = list(deepcopy(set(stmts)))
        # Group statements according to whether they are matches (differing
        # only in their evidence).
        # Sort the statements in place by matches_key()
        st.sort(key=lambda x: x.matches_key())

        for key, duplicates in itertools.groupby(st,
                                                 key=lambda x: x.matches_key()):
            # Get the first statement and add the evidence of all subsequent
            # Statements to it
            for stmt_ix, stmt in enumerate(duplicates):
                if stmt_ix == 0:
                    first_stmt = stmt
                else:
                    first_stmt.evidence += stmt.evidence
            # This should never be None or anything else
            assert isinstance(first_stmt, Statement)
            unique_stmts.append(first_stmt)
        return unique_stmts

    def combine_related(self, return_toplevel=True):
        """Connect related statements based on their refinement relationships.

        This function takes as a starting point the unique statements (with
        duplicates removed) and returns a modified flat list of statements
        containing only those statements which do not represent a refinement of
        other existing statements. In other words, the more general versions of
        a given statement do not appear at the top level, but instead are
        listed in the `supports` field of the top-level statements.

        If :py:attr:`unique_stmts` has not been initialized with the
        de-duplicated statements, :py:meth:`combine_duplicates` is called
        internally.

        After this function is called the attribute :py:attr:`related_stmts` is
        set as a side-effect.

        The procedure for combining statements in this way involves a series
        of steps:

        1. The statements are grouped by type (e.g., Phosphorylation) and
           each type is iterated over independently.
        2. Statements of the same type are then grouped according to their
           Agents' entity hierarchy component identifiers. For instance,
           ERK, MAPK1 and MAPK3 are all in the same connected component in the
           entity hierarchy and therefore all Statements of the same type
           referencing these entities will be grouped. This grouping assures
           that relations are only possible within Statement groups and
           not among groups. For two Statements to be in the same group at
           this step, the Statements must be the same type and the Agents at
           each position in the Agent lists must either be in the same
           hierarchy component, or if they are not in the hierarchy, must have
           identical entity_matches_keys. Statements with None in one of the
           Agent list positions are collected separately at this stage.
        3. Statements with None at either the first or second position are
           iterated over. For a statement with a None as the first Agent,
           the second Agent is examined; then the Statement with None is
           added to all Statement groups with a corresponding component or
           entity_matches_key in the second position. The same procedure is
           performed for Statements with None at the second Agent position.
        4. The statements within each group are then compared; if one
           statement represents a refinement of the other (as defined by the
           `refinement_of()` method implemented for the Statement), then the
           more refined statement is added to the `supports` field of the more
           general statement, and the more general statement is added to the
           `supported_by` field of the more refined statement.
        5. A new flat list of statements is created that contains only those
           statements that have no `supports` entries (statements containing
           such entries are not eliminated, because they will be retrievable
           from the `supported_by` fields of other statements). This list
           is returned to the caller.

        .. note:: Subfamily relationships must be consistent across arguments

            For now, we require that merges can only occur if the *isa*
            relationships are all in the *same direction for all the agents* in
            a Statement. For example, the two statement groups: `RAF_family ->
            MEK1` and `BRAF -> MEK_family` would not be merged, since BRAF
            *isa* RAF_family, but MEK_family is not a MEK1. In the future this
            restriction could be revisited.

        Parameters
        ----------
        return_toplevel : bool
            If True only the top level statements are returned.
            If False, all statements are returned. Default: True

        Returns
        -------
        list of :py:class:`indra.statement.Statement`
            The returned list contains Statements representing the more
            concrete/refined versions of the Statements involving particular
            entities. The attribute :py:attr:`related_stmts` is also set to
            this list. However, if return_toplevel is False then all
            statements are returned, irrespective of level of specificity.
            In this case the relationships between statements can
            be accessed via the supports/supported_by attributes.

        Examples
        --------
        A more general statement with no information about a Phosphorylation
        site is identified as supporting a more specific statement:

        >>> from indra.preassembler.hierarchy_manager import hierarchies
        >>> braf = Agent('BRAF')
        >>> map2k1 = Agent('MAP2K1')
        >>> st1 = Phosphorylation(braf, map2k1)
        >>> st2 = Phosphorylation(braf, map2k1, residue='S')
        >>> pa = Preassembler(hierarchies, [st1, st2])
        >>> combined_stmts = pa.combine_related() # doctest:+ELLIPSIS
        >>> combined_stmts
        [Phosphorylation(BRAF(), MAP2K1(), S)]
        >>> combined_stmts[0].supported_by
        [Phosphorylation(BRAF(), MAP2K1())]
        >>> combined_stmts[0].supported_by[0].supports
        [Phosphorylation(BRAF(), MAP2K1(), S)]
        """
        # If unique_stmts is not initialized, call combine_duplicates.
        if not self.unique_stmts:
            self.combine_duplicates()
        unique_stmts = deepcopy(self.unique_stmts)
        eh = self.hierarchies['entity']
        # Make a list of Statement types
        stmts_by_type = collections.defaultdict(lambda: [])
        for stmt in unique_stmts:
            stmts_by_type[type(stmt)].append(stmt)

        group_sizes = []
        largest_group = None
        largest_group_size = 0
        num_stmts = len(unique_stmts)
        related_stmts = []
        # Each Statement type can be preassembled independently
        for stmt_type, stmts_this_type in stmts_by_type.items():
            logger.info('Preassembling %s (%s)' %
                        (stmt_type.__name__, len(stmts_this_type)))
            # Dict of stmt group key tuples, indexed by their first Agent
            stmt_by_first = collections.defaultdict(lambda: [])
            # Dict of stmt group key tuples, indexed by their second Agent
            stmt_by_second = collections.defaultdict(lambda: [])
            # Dict of statements with None first, with second Agent as keys
            none_first = collections.defaultdict(lambda: [])
            # Dict of statements with None second, with first Agent as keys
            none_second = collections.defaultdict(lambda: [])
            # The dict of all statement groups, with tuples of components
            # or entity_matches_keys as keys
            stmt_by_group = collections.defaultdict(lambda: [])
            # Iterate over the Statements and build the entity key tuples
            # (hierarchy graph components or entity_matches_keys)
            # used to group them
            for stmt in stmts_this_type:
                entities = []
                for i, a in enumerate(stmt.agent_list()):
                    # Entity is None: add the None to the entities list
                    if a is None and stmt_type != Complex:
                        entities.append(a)
                        continue
                    # Entity is not None, but could be ungrounded or not
                    # in a family
                    else:
                        a_ns, a_id = a.get_grounding()
                        # No grounding available--in this case, use the
                        # entity_matches_key
                        if a_ns is None or a_id is None:
                            entities.append(a.entity_matches_key())
                            continue
                        # We have grounding, now check for a component ID
                        uri = eh.get_uri(a_ns, a_id)
                        # This is the component ID corresponding to the agent
                        # in the entity hierarchy
                        component = eh.components.get(uri)
                        # If no component ID, use the entity_matches_key()
                        if component is None:
                            entities.append(a.entity_matches_key())
                        # Component ID, so this is in a family
                        else:
                            # We turn the component ID into a string so that
                            # we can sort it alphabetically along with
                            # entity_matches_keys for Complexes
                            entities.append(str(component))
                # At this point we have an entity list for the Statement.
                # If we're dealing with Complexes, sort the entities and use
                # the sorted list as the stmt_by_group dict key
                if stmt_type == Complex:
                    # There shouldn't be any statements of the type
                    # e.g., Complex([Foo, None, Bar])
                    assert None not in entities
                    assert len(entities) > 0
                    entities.sort()
                    key = tuple(entities)
                    if stmt not in stmt_by_group[key]:
                        stmt_by_group[key].append(stmt)
                # Now look at all other statement types
                # All other statements will have one or two entities
                elif len(entities) == 1:
                    # If only one entity, we only need the one key.
                    # It should not be None!
                    assert None not in entities
                    key = tuple(entities)
                    if stmt not in stmt_by_group[key]:
                        stmt_by_group[key].append(stmt)
                else:
                    # Make sure we only have two entities, and they are not both
                    # None
                    key = tuple(entities)
                    assert len(key) == 2
                    assert key != (None, None)
                    # First agent is None; add the statements to the
                    # none_first dict, indexed by the 2nd entity
                    if key[0] is None and stmt not in none_first[key[1]]:
                        none_first[key[1]].append(stmt)
                    # Second agent is None; add the the statements to the
                    # none_second dict, indexed by the 1st entity
                    elif key[1] is None and stmt not in none_second[key[0]]:
                        none_second[key[0]].append(stmt)
                    # Neither entity is None! Add the statement to the
                    # stmt_by_group dict, and add the key to the corresponding
                    # list of keys in the stmt_by_first and stmt_by_second
                    # lists.
                    elif None not in key:
                        if stmt not in stmt_by_group[key]:
                            stmt_by_group[key].append(stmt)
                        if key not in stmt_by_first[key[0]]:
                            stmt_by_first[key[0]].append(key)
                        if key not in stmt_by_second[key[1]]:
                            stmt_by_second[key[1]].append(key)
            # When we've gotten here, we should have stmt_by_group entries, and
            # we may or may not have stmt_by_first/second and none_first/second
            # dicts filled out (we'll only have them for Statement types that
            # are not Complex and that have two Agents as arguments.
            if none_first:
                # Get the keys associated with stmts having a None first
                # argument
                for second_arg, stmts in none_first.items():
                    # Look for any statement group keys having this second arg
                    second_arg_keys = stmt_by_second[second_arg]
                    # If there are no more specific statements matching this
                    # set of statements with a None first arg, then the
                    # statements with the None first arg deserve to be in
                    # their own group.
                    if not second_arg_keys:
                        stmt_by_group[(None, second_arg)] = stmts
                    # On the other hand, if there are statements with a matching
                    # second arg component, we need to add the None first
                    # statements to all groups with the matching second arg
                    for second_arg_key in second_arg_keys:
                        stmt_by_group[second_arg_key] += stmts
            # Now do the corresponding steps for the statements with None as the
            # second argument:
            if none_second:
                for first_arg, stmts in none_second.items():
                    first_arg_keys = stmt_by_first[first_arg]
                    if not first_arg_keys:
                        stmt_by_group[(first_arg, None)] = stmts
                    for first_arg_key in first_arg_keys:
                        stmt_by_group[first_arg_key] += stmts
            # Now, set supports/supported_by relationships!
            # Keep track of the largest group size for debugging purposes.
            logger.debug('Preassembling %d components' % (len(stmt_by_group)))
            for key, stmts in stmt_by_group.items():
                if len(stmts) > largest_group_size:
                    largest_group_size = len(stmts)
                    largest_group = (key, stmts[0:10])
                group_sizes.append(len(stmts))
                for stmt1, stmt2 in itertools.combinations(stmts, 2):
                    self._set_supports(stmt1, stmt2)
            # Collect top level statements
            toplevel_stmts = [st for st in stmts_this_type if not st.supports]
            logger.debug('%d top level' % len(toplevel_stmts))
            related_stmts += toplevel_stmts

        # Log some stats for debugging purposes
        total_comps = 0
        for g in group_sizes:
            total_comps += g ** 2
        logger.debug("Total comparisons: %s" % total_comps)
        if group_sizes:
            logger.debug("Max group size: %s" % np.max(group_sizes))
            logger.debug("(%.1f %% of all comparisons)" %
                  (100 * ((np.max(group_sizes) ** 2) / float(total_comps))))

        self.related_stmts = related_stmts
        if return_toplevel:
            return self.related_stmts
        else:
            return unique_stmts

    def _set_supports(self, stmt1, stmt2):
        if (stmt2 not in stmt1.supported_by) and \
            stmt1.refinement_of(stmt2, self.hierarchies):
            stmt1.supported_by.append(stmt2)
            stmt2.supports.append(stmt1)
        elif (stmt1 not in stmt2.supported_by) and \
            stmt2.refinement_of(stmt1, self.hierarchies):
            stmt2.supported_by.append(stmt1)
            stmt1.supports.append(stmt2)


def render_stmt_graph(statements, agent_style=None):
    """Render the statement hierarchy as a pygraphviz graph.

    Parameters
    ----------
    stmts : list of :py:class:`indra.statements.Statement`
        A list of top-level statements with associated supporting statements
        resulting from building a statement hierarchy with
        :py:meth:`combine_related`.
    agent_style : dict or None
        Dict of attributes specifying the visual properties of nodes. If None,
        the following default attributes are used::

            agent_style = {'color': 'lightgray', 'style': 'filled',
                           'fontname': 'arial'}

    Returns
    -------
    pygraphviz.AGraph
        Pygraphviz graph with nodes representing statements and edges pointing
        from supported statements to supported_by statements.

    Examples
    --------
    Pattern for getting statements and rendering as a Graphviz graph:

    >>> from indra.preassembler.hierarchy_manager import hierarchies
    >>> braf = Agent('BRAF')
    >>> map2k1 = Agent('MAP2K1')
    >>> st1 = Phosphorylation(braf, map2k1)
    >>> st2 = Phosphorylation(braf, map2k1, residue='S')
    >>> pa = Preassembler(hierarchies, [st1, st2])
    >>> pa.combine_related() # doctest:+ELLIPSIS
    [Phosphorylation(BRAF(), MAP2K1(), S)]
    >>> graph = render_stmt_graph(pa.related_stmts)
    >>> graph.write('example_graph.dot') # To make the DOT file
    >>> graph.draw('example_graph.png', prog='dot') # To make an image

    Resulting graph:

    .. image:: /images/example_graph.png
        :align: center
        :alt: Example statement graph rendered by Graphviz

    """
    # Set the default agent formatting properties
    if agent_style is None:
        agent_style = {'color': 'lightgray', 'style': 'filled',
                       'fontname': 'arial'}
    # Sets to store all of the nodes and edges as we recursively process all
    # of the statements
    nodes = set([])
    edges = set([])
    # Recursive function for processing all statements
    def process_stmt(stmt):
        nodes.add(stmt)
        for sby_ix, sby_stmt in enumerate(stmt.supported_by):
            edges.add((str(stmt.matches_key()), str(sby_stmt.matches_key())))
            process_stmt(sby_stmt)
    # Process all of the top-level statements, getting the supporting statements
    # recursively
    for stmt in statements:
        process_stmt(stmt)
    # Add the nodes and edges to the graph
    try:
        graph = pgv.AGraph(name='statements', directed=True, rankdir='LR')
    except NameError:
        logger.error('Cannot generate graph because '
                     'pygraphviz could not be imported.')
        return None
    for node in nodes:
        graph.add_node(str(node.matches_key()), label=str(node), **agent_style)
    graph.add_edges_from(edges)
    return graph


def flatten_stmts(stmts):
    """Return the full set of unique stms in a pre-assembled stmt graph.

    The flattened list of of statements returned by this function can be
    compared to the original set of unique statements to make sure no
    statements have been lost during the preassembly process.

    Parameters
    ----------
    stmts : list of :py:class:`indra.statements.Statement`
        A list of top-level statements with associated supporting statements
        resulting from building a statement hierarchy with
        :py:meth:`combine_related`.

    Returns
    -------
    stmts : list of :py:class:`indra.statements.Statement`
        List of all statements contained in the hierarchical statement graph.

    Examples
    --------
    Calling :py:meth:`combine_related` on two statements results in one
    top-level statement; calling :py:func:`flatten_stmts` recovers both:

    >>> from indra.preassembler.hierarchy_manager import hierarchies
    >>> braf = Agent('BRAF')
    >>> map2k1 = Agent('MAP2K1')
    >>> st1 = Phosphorylation(braf, map2k1)
    >>> st2 = Phosphorylation(braf, map2k1, residue='S')
    >>> pa = Preassembler(hierarchies, [st1, st2])
    >>> pa.combine_related() # doctest:+ELLIPSIS
    [Phosphorylation(BRAF(), MAP2K1(), S)]
    >>> flattened = flatten_stmts(pa.related_stmts)
    >>> flattened.sort(key=lambda x: x.matches_key())
    >>> flattened
    [Phosphorylation(BRAF(), MAP2K1()), Phosphorylation(BRAF(), MAP2K1(), S)]
    """
    total_stmts = set(stmts)
    for stmt in stmts:
        if stmt.supported_by:
            children = flatten_stmts(stmt.supported_by)
            total_stmts = total_stmts.union(children)
    return list(total_stmts)


def _flatten_evidence_for_stmt(stmt):
    total_evidence = set(stmt.evidence)
    for supp_stmt in stmt.supported_by:
        child_evidence = _flatten_evidence_for_stmt(supp_stmt)
        total_evidence = total_evidence.union(child_evidence)
    return list(total_evidence)


def flatten_evidence(stmts):
    """Add evidence from *supporting* stmts to evidence for *supported* stmts.

    Parameters
    ----------
    stmts : list of :py:class:`indra.statements.Statement`
        A list of top-level statements with associated supporting statements
        resulting from building a statement hierarchy with
        :py:meth:`combine_related`.

    Returns
    -------
    stmts : list of :py:class:`indra.statements.Statement`
        Statement hierarchy identical to the one passed, but with the
        evidence lists for each statement now containing all of the evidence
        associated with the statements they are supported by.

    Examples
    --------
    Flattening evidence adds the two pieces of evidence from the supporting
    statement to the evidence list of the top-level statement:

    >>> from indra.preassembler.hierarchy_manager import hierarchies
    >>> braf = Agent('BRAF')
    >>> map2k1 = Agent('MAP2K1')
    >>> st1 = Phosphorylation(braf, map2k1,
    ... evidence=[Evidence(text='foo'), Evidence(text='bar')])
    >>> st2 = Phosphorylation(braf, map2k1, residue='S',
    ... evidence=[Evidence(text='baz'), Evidence(text='bak')])
    >>> pa = Preassembler(hierarchies, [st1, st2])
    >>> pa.combine_related() # doctest:+ELLIPSIS
    [Phosphorylation(BRAF(), MAP2K1(), S)]
    >>> [e.text for e in pa.related_stmts[0].evidence] # doctest:+IGNORE_UNICODE
    ['baz', 'bak']
    >>> flattened = flatten_evidence(pa.related_stmts)
    >>> sorted([e.text for e in flattened[0].evidence]) # doctest:+IGNORE_UNICODE
    ['bak', 'bar', 'baz', 'foo']
    """
    # Copy all of the statements--these will be the ones where we update
    # the evidence lists
    copied_stmts = deepcopy(stmts)
    for stmt in stmts:
        total_evidence = _flatten_evidence_for_stmt(stmt)
        stmt.evidence = total_evidence
    return stmts
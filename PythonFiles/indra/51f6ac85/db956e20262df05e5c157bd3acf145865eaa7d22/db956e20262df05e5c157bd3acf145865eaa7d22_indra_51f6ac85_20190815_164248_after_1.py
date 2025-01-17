import logging
import pandas as pd
from .net import IndraNet
from indra.statements import *
from itertools import permutations
from collections import OrderedDict, defaultdict


logger = logging.getLogger(__name__)
NS_PRIORITY_LIST = (
    'FPLX', 'HGNC', 'UP', 'CHEBI', 'GO', 'MESH', 'HMDB', 'PUBCHEM')

default_sign_dict = {'Activation': 0,
                     'Inhibition': 1,
                     'IncreaseAmount': 0,
                     'DecreaseAmount': 1}


def get_ag_ns_id(ag):
    """Return a tuple of name space, id from an Agent's db_refs."""
    for ns in NS_PRIORITY_LIST:
        if ns in ag.db_refs:
            return ns, ag.db_refs[ns]
    return 'TEXT', ag.name


class IndraNetAssembler():
    """Assembler to create an IndraNet object from a list of INDRA statements.

    Parameters
    ----------
    statements : list[indra.statements.Statement]
        A list of INDRA Statements to be assembled.

    Attributes
    ----------
    model : IndraNet
        An IndraNet graph object assembled by this class.
    """

    def __init__(self, statements=None):
        self.statements = statements if statements else []
        self.model = None

    def add_statements(self, stmts):
        """Add INDRA Statements to the assembler's list of statements.

        Parameters
        ----------
        stmts : list[indra.statements.Statement]
            A list of :py:class:`indra.statements.Statement`
            to be added to the statement list of the assembler.
        """
        self.statements += stmts

    def make_model(self, exclude_stmts=None, complex_members=3,
                   graph_type='multi_graph', sign_dict=None,
                   belief_flattening=None, weight_flattening=None):
        """Assemble an IndraNet graph object.

        Parameters
        ----------
        exclude_stmts : list[str]
            A list of statement type names to not include in the graph.
        complex_members : int
            Maximum allowed size of a complex to be included in the graph.
            All complexes larger than complex_members will be rejected. For
            accepted complexes, all permutations of their members will be added
            as edges.
        graph_type : str
            Specify the type of graph to assemble. Chose from 'multi_graph'
            (default), 'digraph', 'signed'.
        sign_dict : dict
            A dictionary mapping a Statement type to a sign to be used for
            the edge. This parameter is only used with the 'signed' option.
            See IndraNet.to_signed_graph for more info.
        belief_flattening : str|function(G, edge)
            The method to use when updating the belief for the flattened edge.

            If a string is provided, it must be one of the predefined options
            'simple_scorer' or 'complementary_belief'.

            If a function is provided, it must take the flattened graph 'G'
            and an edge 'edge' to perform the belief flattening on and return
            a number:

            >>> def belief_flattening(G, edge):
            ...     # Return the average belief score of the constituent edges
            ...     all_beliefs = [s['belief']
            ...         for s in G.edges[edge]['statements']]
            ...     return sum(all_beliefs)/len(all_beliefs)

        weight_flattening : function(G)
            A function taking at least the graph G as an argument and
            returning G after adding edge weights as an edge attribute to the
            flattened edges using the reserved keyword 'weight'.

            Example:

            >>> def weight_flattening(G):
            ...     # Sets the flattened weight to the average of the
            ...     # inverse source count
            ...     for edge in G.edges:
            ...         w = [1/s['evidence_count']
            ...             for s in G.edges[edge]['statements']]
            ...         G.edges[edge]['weight'] = sum(w)/len(w)
            ...     return G


        Returns
        -------
        model : IndraNet
            IndraNet graph object.
        """
        df = self.make_df(exclude_stmts, complex_members)
        if graph_type == 'multi_graph':
            model = IndraNet.from_df(df)
        elif graph_type == 'digraph':
            model = IndraNet.digraph_from_df(
                df=df,
                flattening_method=belief_flattening,
                weight_mapping=weight_flattening
            )
        elif graph_type == 'signed':
            sign_dict = default_sign_dict if not sign_dict else sign_dict
            model = IndraNet.signed_from_df(df, sign_dict=sign_dict,
                                            flattening_method=belief_flattening,
                                            weight_mapping=weight_flattening)
        else:
            raise TypeError('Have to specify one of \'multi_graph\', '
                            '\'digraph\' or \'signed\' when providing graph '
                            'type.')
        return model

    def make_df(self, exclude_stmts=None, complex_members=3):
        """Create a dataframe containing information extracted from assembler's
        list of statements necessary to build an IndraNet.

        Parameters
        ----------
        exclude_stmts : list[str]
            A list of statement type names to not include into a dataframe.
        complex_members : int
            Maximum allowed size of a complex to be included in the data
            frame. All complexes larger than complex_members will be rejected.
            For accepted complexes, all permutations of their members will be
            added as dataframe records.

        Returns
        -------
        df : pd.DataFrame
            Pandas DataFrame object containing information extracted from
            statements.
        """
        rows = []
        if exclude_stmts:
            exclude_types = tuple(
                get_statement_by_name(st_type) for st_type in exclude_stmts)
        else:
            exclude_types = ()
        for stmt in self.statements:
            # Exclude statements from given exclude list
            if isinstance(stmt, exclude_types):
                logger.debug('Skipping a statement of a type %s.'
                             % type(stmt).__name__)
                continue
            agents = stmt.agent_list()
            not_none_agents = [a for a in agents if a is not None]
            # Exclude statements with less than 2 agents
            if len(not_none_agents) < 2:
                continue
            # Handle complexes
            if isinstance(stmt, Complex):
                # Do not add complexes with more members than complex_members
                if len(not_none_agents) > complex_members:
                    logger.debug('Skipping a complex with %d members.'
                                 % len(not_none_agents))
                    continue
                else:
                    # add every permutation
                    pairs = permutations(not_none_agents, 2)
            else:
                pairs = [not_none_agents]
            for (agA, agB) in pairs:
                agA_ns, agA_id = get_ag_ns_id(agA)
                agB_ns, agB_id = get_ag_ns_id(agB)
                stmt_type = type(stmt).__name__
                row = OrderedDict([
                    ('agA_name', agA.name),
                    ('agB_name', agB.name),
                    ('agA_ns', agA_ns),
                    ('agA_id', agA_id),
                    ('agB_ns', agB_ns),
                    ('agB_id', agB_id),
                    ('stmt_type', stmt_type),
                    ('evidence_count', len(stmt.evidence)),
                    ('stmt_hash', stmt.get_hash(refresh=True)),
                    ('belief', stmt.belief),
                    ('source_counts', _get_source_counts(stmt))])
                rows.append(row)
        df = pd.DataFrame.from_dict(rows)
        return df


def _get_source_counts(stmt):
    source_counts = defaultdict(int)
    for ev in stmt.evidence:
        source_counts[ev.source_api] += 1
    return source_counts

import logging

import pandas as pd
import networkx as nx

from indra.belief import SimpleScorer
from indra.statements import Evidence
from indra.statements import Statement

logger = logging.getLogger(__name__)
default_sign_dict = {'Activation': 0,
                     'Inhibition': 1,
                     'IncreaseAmount': 0,
                     'DecreaseAmount': 1}
scorer = SimpleScorer()


class IndraNet(nx.MultiDiGraph):
    """A Networkx representation of INDRA Statements."""
    def __init__(self, incoming_graph_data=None, **attr):
        super().__init__(incoming_graph_data, **attr)
        self._is_multi = True
        self.mandatory_columns = ['agA_name', 'agB_name', 'agA_ns', 'agA_id',
                                  'agB_ns', 'agB_id', 'stmt_type',
                                  'evidence_count', 'stmt_hash', 'belief',
                                  'source_counts']

    @classmethod
    def from_df(cls, df):
        """Create an IndraNet MultiDiGraph from a pandas DataFrame.

        Returns an instance of IndraNet with graph data filled out from a
        dataframe containing pairwise interactions.

        Parameters
        ----------
        df : pd.DataFrame
            A :py:class:`pandas.DataFrame` with each row containing node and
            edge data for one edge. Indices are used to distinguish
            multiedges between a pair of nodes. Any columns not part of the
            mandatory columns are considered extra attributes. Columns
            starting with 'agA\_' or 'agB\_' (excluding the agA/B_name) will
            be added to its respective nodes as node attributes. Any other
            columns will be added as edge attributes.

        Returns
        -------
        IndraNet
            An IndraNet object
        """
        graph = cls()
        mandatory_columns = graph.mandatory_columns
        if not set(mandatory_columns).issubset(set(df.columns)):
            raise ValueError('Missing one or more columns of %s in data '
                             'frame' % mandatory_columns)
        node_keys = {'agA': set(), 'agB': set()}
        edge_keys = set()
        for key in df.columns:
            if key not in mandatory_columns:
                if key.startswith('agA_'):
                    node_keys['agA'].add(key)
                if key.startswith('agB_'):
                    node_keys['agB'].add(key)
                if not key.startswith('ag'):
                    edge_keys.add(key)
        index = 0
        skipped = 0
        for index, row in df.iterrows():
            if row['agA_name'] is None or row['agB_name'] is None:
                skipped += 1
                logger.warning('None found as node (index %d)' % index)
                continue
            # Check and get node/edge attributes
            nodeA_attr = {}
            nodeB_attr = {}
            edge_attr = {}
            if node_keys['agA']:
                for key in node_keys['agA']:
                    nodeA_attr[key] = row[key]
            if node_keys['agB']:
                for key in node_keys['agB']:
                    nodeB_attr[key] = row[key]
            if edge_keys:
                for key in edge_keys:
                    edge_attr[key] = row[key]

            # Add non-existing nodes
            if row['agA_name'] not in graph.nodes:
                graph.add_node(row['agA_name'], ns=row['agA_ns'],
                               id=row['agA_id'], **nodeA_attr)
            if row['agB_name'] not in graph.nodes:
                graph.add_node(row['agB_name'], ns=row['agB_ns'],
                               id=row['agB_id'], **nodeB_attr)
            # Add edges
            ed = {'u_for_edge': row['agA_name'],
                  'v_for_edge': row['agB_name'],
                  'stmt_hash': row['stmt_hash'],
                  'stmt_type': row['stmt_type'],
                  'evidence_count': row['evidence_count'],
                  'belief': row['belief'],
                  'source_counts': row['source_counts'],
                  **edge_attr}
            graph.add_edge(**ed)
        if skipped:
            logger.warning('Skipped %d edges with None as node' % skipped)
        return graph

    def to_digraph(self):
        """Flatten the IndraNet to a DiGraph

        Returns
        -------
        G : IndraNet(nx.DiGraph)
            An IndraNet graph flattened to a DiGraph
        """
        G = nx.DiGraph()
        for u, v, data in self.edges(data=True):
            if G.has_edge(u, v):
                G[u][v]['statements'].append(data)
            else:
                G.add_edge(u, v, statements=[data])
        return self._update_edge_belief(G)

    def to_signed_graph(self, sign_dict=default_sign_dict):
        """Flatten the IndraNet to a signed graph.
        
        Parameters
        ----------
        sign_dict : dict
            A dictionary mapping a Statement type to a sign to be used for
            the edge. By default only Activation and IncreaseAmount are added
            as positive edges and Inhibition and DecreaseAmount are added as
            negative edges, but a user can pass any other Statement types in
            a dictionary.

        Returns
        -------
        SG : IndraNet(nx.MultiDiGraph)
            An IndraNet graph flattened to a signed graph
        """
        SG = nx.MultiDiGraph()
        for u, v, data in self.edges(data=True):
            if data['stmt_type'] not in sign_dict:
                continue
            sign = sign_dict[data['stmt_type']]
            if SG.has_edge(u, v, sign):
                SG[u][v][sign]['statements'].append(data)
            else:
                SG.add_edge(u, v, sign, statements=[data], sign=sign)
        return self._update_edge_belief(SG)

    @classmethod
    def digraph_from_df(cls, df):
        """Create a digraph from a pandas DataFrame."""
        net = cls.from_df(df)
        return net.to_digraph()

    @classmethod
    def signed_from_df(cls, df, sign_dict=default_sign_dict):
        """Create a signed graph from a pandas DataFrame."""
        net = cls.from_df(df)
        return net.to_signed_graph(sign_dict=sign_dict)

    @staticmethod
    def _update_edge_belief(G):
        """G must be or be a child of an nx.Graph object"""

        # Aggregate belief using fake statements, one statement per edge
        for e in G.edges:
            # Aggregate source counts
            evidence_list = []
            for stmt_data in G.edges[e]['statements']:
                for k, v in stmt_data['source_counts'].items():
                    for _ in range(v):
                        evidence_list.append(Evidence(source_api=k))
            G.edges[e]['belief'] = scorer.score_statement(
                st=Statement(evidence=evidence_list))
        return G
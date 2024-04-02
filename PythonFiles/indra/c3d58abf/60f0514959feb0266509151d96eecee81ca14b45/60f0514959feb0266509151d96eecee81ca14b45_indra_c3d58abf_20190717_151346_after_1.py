import networkx as nx
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class IndraNet(nx.MultiDiGraph):
    def __init__(self, incoming_graph_data=None, **attr):
        super().__init__(incoming_graph_data, **attr)
        self._is_multi = True

    def _add_node(self, name, ns, id, **attr):
        all_attr = {'ns': ns, 'id': id, **attr}
        self.add_node(node_for_adding=name, **all_attr)

    def _add_edge(self, u, v, key=None, **attr):
        self.add_edge(u_for_edge=u, v_for_edge=v, key=key, **attr)

    @classmethod
    def from_df(cls, df=pd.DataFrame(), belief_dict=None, strat_ev_dict=None,
                multi=True):
        """idea: enforce pair of ('agA_<attribute>', 'agB_<attribute>') for
        node attributes, otherwise considered edge attribute

        :param df: pd.DataFrame
        :param belief_dict:
        :param strat_ev_dict:
        :param multi:
        :return:
        """
        mandatory_columns = ['agA_name', 'agB_name', 'agA_ns', 'agA_id',
                             'agB_ns', 'agB_id', 'stmt_type', 'evidence_count',
                             'hash', 'belief', 'evidence']
        if not set(mandatory_columns).issubset(set(df.columns)):
            raise ValueError('Missing required columns in data frame')
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
            # Add non-existing nodes
            if row['agA_name'] not in cls.nodes:
                cls._add_node(row['agA_name'], row['agA_ns'], row['agA_id'])
            if row['agB_name'] not in cls.nodes:
                cls._add_node(row['agB_name'], row['agB_ns'], row['agB_id'])
            # Add edges
            ed = {'u': row['agA_name'],
                  'v': row['agB_name'],
                  'stmt_type': row['stmt_type'],
                  'evidence_count': row['evidence_count'],
                  'evidence': row['evidence'],
                  'belief': row['belief']}
            cls._add_edge(**ed)
        if skipped:
            logger.warning('Skipped %d edges with None as node' % skipped)
        return cls

    @classmethod
    def to_type_graph(cls):
        # Will wrap 'from_df' and collapse edges as necessary
        cls.from_df()
        return cls

    def is_multigraph(self):
        return self._is_multi
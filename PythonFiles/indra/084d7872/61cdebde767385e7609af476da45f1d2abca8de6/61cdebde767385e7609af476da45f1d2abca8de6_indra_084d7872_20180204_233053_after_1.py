from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str
from networkx import MultiDiGraph

def im_json_to_graph(im_json):
    """Return networkx graph from Kappy's influence map JSON.

    Parameters
    ----------
    im_json : dict
        A JSON dict which contains an influence map generated by Kappy.

    Returns
    -------
    graph : networkx.MultiDiGraph
        A graph representing the influence map.
    """
    imap_data = im_json['influence map']['map']

    # Initialize the graph
    graph = MultiDiGraph()

    id_node_dict = {}
    # Add each node to the graph
    for node_dict in imap_data['nodes']:
        # There is always just one entry here with the node type e.g. "rule"
        # as key, and all the node data as the value
        node_type, node = list(node_dict.items())[0]
        # Add the node to the graph with its label and type
        graph.add_node(node['label'], node_type=node_type)
        # Save the key of the node to refer to it later
        new_key = '%s%s' % (node_type, node['id'])
        id_node_dict[new_key] = node['label']


    def add_edges(link_list, edge_sign):
        for link_dict in link_list:
            source = link_dict['source']
            for target_dict in link_dict['target map']:
                target = target_dict['target']
                src_id = '%s%s' % list(source.items())[0]
                tgt_id = '%s%s' % list(target.items())[0]
                graph.add_edge(id_node_dict[src_id], id_node_dict[tgt_id],
                               sign=edge_sign)

    # Add all the edges from the positive and negative influences
    add_edges(imap_data['wake-up map'], 1)
    add_edges(imap_data['inhibition map'], -1)

    return graph

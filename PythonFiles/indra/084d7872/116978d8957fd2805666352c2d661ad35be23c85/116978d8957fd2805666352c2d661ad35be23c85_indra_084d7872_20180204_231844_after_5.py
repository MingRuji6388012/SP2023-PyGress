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

    # Add each node to the graph
    id_node_dict = {}
    for node_dict in imap_data['nodes']:
        key = list(node_dict.keys())[0]
        graph.add_node(node_dict[key]['label'], node_type=key)
        new_key = key + str(node_dict[key]['id'])
        id_node_dict[new_key] = node_dict[key]['label']


    def add_edges(link_list, edge_sign):
        for link_dict in link_list:
            source = link_dict['source']
            for target_dict in link_dict['target map']:
                target = target_dict['target']
                src_id = list(source.keys())[0] \
                    + str(list(source.values())[0])
                tgt_id = list(target.keys())[0] \
                    + str(list(target.values())[0])
                graph.add_edge(id_node_dict[src_id], id_node_dict[tgt_id],
                               sign = edge_sign)

    add_edges(imap_data['wake-up map'], 1)
    add_edges(imap_data['inhibition map'], -1)

    return graph

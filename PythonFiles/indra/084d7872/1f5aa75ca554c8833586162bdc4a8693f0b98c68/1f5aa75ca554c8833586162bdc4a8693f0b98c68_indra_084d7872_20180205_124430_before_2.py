from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str
from networkx import MultiDiGraph
from pygraphviz import AGraph


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
        attrs = {'fillcolor': '#b7d2ff' if node_type == 'rule' else '#cdffc9',
                 'shape': 'box' if node_type == 'rule' else 'oval',
                 'style': 'filled'}
        graph.add_node(node['label'], node_type=node_type, **attrs)
        # Save the key of the node to refer to it later
        new_key = '%s%s' % (node_type, node['id'])
        id_node_dict[new_key] = node['label']

    def add_edges(link_list, edge_sign):
        attrs = {'sign': edge_sign,
                 'color': 'green' if edge_sign == 1 else 'red',
                 'arrowhead': 'normal' if edge_sign == 1 else 'tee'}
        for link_dict in link_list:
            source = link_dict['source']
            for target_dict in link_dict['target map']:
                target = target_dict['target']
                src_id = '%s%s' % list(source.items())[0]
                tgt_id = '%s%s' % list(target.items())[0]
                graph.add_edge(id_node_dict[src_id], id_node_dict[tgt_id],
                               **attrs)

    # Add all the edges from the positive and negative influences
    add_edges(imap_data['wake-up map'], 1)
    add_edges(imap_data['inhibition map'], -1)

    return graph


def cm_json_to_graph(im_json):
    """Return pygraphviz Agraph from Kappy's contact map JSON.

    Parameters
    ----------
    im_json : dict
        A JSON dict which contains a contact map generated by Kappy.

    Returns
    -------
    graph : pygraphviz.Agraph
        A graph representing the contact map.
    """
    cmap_data = im_json['contact map']['map']

    # Initialize the graph
    graph = AGraph()

    # We need to build a map of sites to be able to reference them
    # from the port links
    site_map = {}
    # We also collect all the edges here
    edges = []
    for node_idx, node in enumerate(cmap_data):
        for site_idx, site in enumerate(node['node_sites']):
            # We generate a unique ID based on the parent node and the
            # specific site
            site_id = '%s/%s' % (node['node_type'], site['site_name'])
            site_map[(node_idx, site_idx)] = site_id
            # Each port link is an edge from the current site to the
            # specified site
            if not site['site_type'] or not site['site_type'][0] == 'port':
                continue
            for port_link in site['site_type'][1]['port_links']:
                edge = ((node_idx, site_idx), tuple(port_link))
                edges.append(edge)

    for source, target in edges:
        source_name = site_map[source]
        target_name = site_map[target]
        graph.add_edge(source_name, target_name)
    return graph
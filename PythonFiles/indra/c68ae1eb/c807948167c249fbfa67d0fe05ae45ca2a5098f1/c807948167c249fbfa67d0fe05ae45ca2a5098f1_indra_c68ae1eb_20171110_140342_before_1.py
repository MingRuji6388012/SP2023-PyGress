import random
import pickle
import numpy as np
import networkx as nx
from matplotlib import pyplot as plt
from indra.util import _require_python3
from indra.util import read_unicode_csv, write_unicode_csv
from indra.util import plot_formatting as pf
from indra.explanation import paths_graph as pg


def stmts_to_digraph(stmts):
    digraph = nx.MultiDiGraph()
    for stmt in stmts:
        agent_names = [a.name for a in stmt.agent_list() if a is not None]
        if len(agent_names) != 2:
            continue
        digraph.add_edge(agent_names[0], agent_names[1],
                         attr_dict={'uuid': stmt.uuid})
    return digraph


def filtered_stmts(stmts, max_depth=3, source, target):
    g = stmts_to_digraph(stmts)

    #scc_sizes = [len(scc) for scc in nx.strongly_connected_components(g)]
    source = 'BRAF'
    target = 'JUN'
    f_level, b_level = pg.get_reachable_sets(g, source, target,
                                             max_depth=max_depth, signed=False)
    stmt_uuids = set()
    stmt_nodes = set()
    stmt_uuid_nums = []
    stmt_node_nums = []
    # Iterate over various path lengths
    for length in range(1, max_depth+1):
        print("Generating paths_graph for length %d" % length)
        this_pg = pg.paths_graph(g, source, target, length, f_level, b_level,
                                 signed=False)
        # Get nodes for this length PG
        nodes_this_length = set([n[1] for n in this_pg])
        # Get stmt UUIDs for this length PG
        stmt_uuids_this_length = set()
        for u, v in this_pg.edges():
            u_name, v_name = (u[1], v[1])
            multiedge_data = g.get_edge_data(u_name, v_name)
            for edge_data in multiedge_data.values():
                stmt_uuids_this_length.add((u_name, edge_data['uuid'], v_name))
        stmt_uuids |= stmt_uuids_this_length
        stmt_nodes |= nodes_this_length
        # Get counts for this depth
        # Terminate the loop if we've saturated the number of edges
        if stmt_uuid_nums and stmt_uuid_nums[-1] != 0 and \
                len(stmt_uuids) == stmt_uuid_nums[-1]:
            break
        stmt_uuid_nums.append(len(stmt_uuids))
        stmt_node_nums.append(len(stmt_nodes))
        print("Paths of length %d: %d uuids" %
              (length, len(stmt_uuids_this_length)))

    return (g, stmt_uuids, stmt_nodes, stmt_node_nums, stmt_uuid_nums)


def plot_results(g, stmt_uuids, stmt_nodes, stmt_node_nums, stmt_uuid_nums):
    norm_node_counts = np.array(stmt_node_nums) / len(g)
    norm_uuid_counts = np.array(stmt_uuid_nums) / len(g.edges())

    pf.set_fig_params()
    plt.ion()
    lengths = range(len(norm_uuid_counts))
    plt.figure(figsize=(2, 2), dpi=150)
    plt.plot(lengths, norm_uuid_counts, color='orange', alpha=0.8,
             label='Statements')
    plt.plot(lengths, norm_node_counts, color='blue', alpha=0.8, label='Nodes')
    plt.legend(loc='upper left', fontsize=pf.fontsize, frameon=False)
    ax = plt.gca()
    pf.format_axis(ax)
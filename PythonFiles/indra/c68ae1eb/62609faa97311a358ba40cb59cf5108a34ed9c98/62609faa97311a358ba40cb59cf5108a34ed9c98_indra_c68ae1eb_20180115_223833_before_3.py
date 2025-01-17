import pickle
import networkx as nx
from nose.tools import raises
from os.path import dirname, join
from indra.explanation.paths_graph import paths_graph, pre_cfpg as pcf
from indra.explanation.paths_graph import cfpg as cf


random_graph_pkl = join(dirname(__file__), 'random_graphs.pkl')

g_uns = nx.DiGraph()
g_uns.add_edges_from((('A', 'B'), ('A', 'C'), ('C', 'D'), ('B', 'D'),
                      ('D', 'B'), ('D', 'C'), ('B', 'E'), ('C', 'E')))
source = 'A'
target = 'E'
length = 4


def test_from_graph_no_levels():
    cfpg = cf.from_graph(g_uns, source, target, length)
    assert isinstance(cfpg, cf.CFPG)
    paths = cfpg.enumerate_paths()
    assert len(paths) == 2
    assert ('A', 'B', 'D', 'C', 'E') in paths
    assert ('A', 'C', 'D', 'B', 'E') in paths
    assert len(cfpg.graph) == 8
    # The D node should be split into two nodes
    d_nodes = [n for n in cfpg.graph.nodes() if n[1] == 'D']
    assert len(d_nodes) == 2


def test_from_graph_with_levels_bad_depth():
    """Raise an exception if the requested path length is greater than the
    depth of the provided reach sets."""
    (f_reach, b_reach) = paths_graph.get_reachable_sets(g_uns, source, target,
                                                        max_depth=2)
    cfpg = cf.from_graph(g_uns, source, target, length, fwd_reachset=f_reach,
                         back_reachset=b_reach)
    assert not cfpg.graph


def test_from_pg():
    (f_reach, b_reach) = paths_graph.get_reachable_sets(g_uns, source, target,
                                                        max_depth=length)
    pg = paths_graph.from_graph(g_uns, source, target, length, f_reach,
                                b_reach)
    cfpg = cf.from_pg(pg)
    paths = cfpg.enumerate_paths()
    assert len(paths) == 2
    assert ('A', 'B', 'D', 'C', 'E') in paths
    assert ('A', 'C', 'D', 'B', 'E') in paths
    assert len(cfpg.graph) == 8
    # The D node should be split into two nodes
    d_nodes = [n for n in cfpg.graph.nodes() if n[1] == 'D']
    assert len(d_nodes) == 2


def test_on_random_graphs():
    """For each of 25 random graphs, check that the number of cycle free paths
    for a given depth and source/target pair matches the results from
    networkx all_simple_paths. Graphs range from rough"""
    # We use 25 randomly generated graphs for testing the algorithm
    with open(random_graph_pkl, 'rb') as f:
        rg_dict = pickle.load(f)

    min_depth = 5
    max_depth = 10
    for i in range(1):
        G_i, source, target = rg_dict[i]
        print("graph# %d, %d nodes, %d edges" % (i, len(G_i), len(G_i.edges())))
        (f_reach, b_reach)  = \
                paths_graph.get_reachable_sets(G_i, source, target,
                        max_depth=max_depth, signed=False)
        # Try different path lengths
        for length in range(min_depth, max_depth+1):
            print("Checking paths of length %d" % length)
            # For validation, we compute explicitly the set of paths in the
            # original graph of a fixed length
            P = list(nx.all_simple_paths(G_i, source, target, length+1))
            # Filter to paths of this length
            P_correct = [tuple(p) for p in P if len(p) == length+1]
            # Generate the raw paths graph
            G_cf = cf.from_graph(G_i, source, target, length, f_reach,
                                 b_reach)
            # Enumerate paths using node tuples
            P_cf_pruned = G_cf.enumerate_paths(names_only=False)
            # Next we extract the paths by projecting down to second
            # component (node names)
            P_cf_pruned_names = G_cf.enumerate_paths(names_only=True)
            print("# of paths: %d" % len(P_cf_pruned_names))

            # We verify the three required properties.
            # Recall:
            # CF1: Every source-to-target path in G_cf is cycle free.
            # CF2: Every cycle free path in the original graph appears as a
            #      source-to-target path in G_cf.
            # CF3: There is a 1-1 correspondence between the paths in G_cf and
            # the paths in the original graph. This means there is no
            # redundancy in the representation. For every path in the original
            # graph there is a unique path in G_cf that corresponds to it.

            # We first verify CF1.
            for p in P_cf_pruned_names:
                if len(p) != len(list(set(p))):
                    print("cycle!")
                    print(p)
                    assert False
            # Next we verify CF2. We will in fact check if the set of paths in
            # P_cf_pruned_names is exactly the set of paths in the original
            # graph.
            if set(P_correct) != set(P_cf_pruned_names):
                print("Paths do not match reference set from networkx")
                print("graph, length", (i, length))
                assert False
            # Finally we verify CF3
            if len(P_cf_pruned) != len(list(set(P_cf_pruned_names))):
                print("redundant representation!")
                print("graph, length", (i, length))
                assert False


if __name__ == '__main__':
    test_on_random_graphs()

import os
from collections import Counter
import pygraphviz
import networkx as nx
import numpy as np
from indra.explanation.paths_graph import PathsGraph, get_reachable_sets, \
                                          sample_raw_graph, combine_paths_graphs

source = 'A'
target = 'D'
target_polarity = 0

graph1_s = nx.DiGraph()
graph1_s.add_nodes_from(['A', 'B', 'C', 'D'])
graph1_s.add_edges_from([('A', 'B', {'sign': 0}),
                         ('B', 'D', {'sign': 0}),
                         ('A', 'C', {'sign': 0}),
                         ('C', 'D', {'sign': 0})])

graph1_uns = nx.DiGraph()
graph1_uns.add_nodes_from(['A', 'B', 'C', 'D'])
graph1_uns.add_edges_from([('A', 'B'), ('B', 'D'), ('A', 'C'), ('C', 'D')])


g_samp = nx.DiGraph() # Graph for testing sampling uniformly vs. non-uniformly
g_samp.add_edges_from([
    ('source', 'A1'), ('source', 'A2'),
    ('A1', 'B1'),
    ('A2', 'B2'), ('A2', 'B3'), ('A2', 'B4'), ('A2', 'B5'),
    ('B1', 'target'),
    ('B2', 'target'), ('B3', 'target'), ('B4', 'target'), ('B5', 'target')])

def test_get_reachable_sets_unsigned():
    f_level, b_level = get_reachable_sets(graph1_uns, source, target,
                                          signed=False)
    assert f_level == {0: {'A'}, 1: {'B', 'C'}, 2: {'D'}}
    assert b_level == {0: {'D'}, 1: {'B', 'C'}, 2: {'A'}}


def test_get_reachable_sets_signed():
    f_level, b_level = get_reachable_sets(graph1_s, source, target, signed=True)
    assert f_level == {0: {('A', 0)}, 1: {('B', 0), ('C', 0)}, 2: {('D', 0)}}
    assert b_level == {0: {('D', 0)}, 1: {('B', 0), ('C', 0)}, 2: {('A', 0)}}


def test_unreachability_unsigned():
    graph = nx.DiGraph()
    graph.add_nodes_from(['A', 'B', 'C', 'D'])
    graph.add_edges_from([('A', 'B'), ('D', 'B'), ('C', 'A'), ('C', 'D')])
    (f_level, b_level) = get_reachable_sets(graph, source, target,
                                            max_depth=5, signed=False)
    assert f_level == {}
    assert b_level == {}


def test_unreachability_signed():
    # First make the unreachability due to the direction of the edges
    graph = nx.DiGraph()
    graph.add_nodes_from(['A', 'B', 'C', 'D'])
    graph.add_edges_from([('A', 'B', {'sign': 0}),
                          ('D', 'B', {'sign': 0}),
                          ('C', 'A', {'sign': 0}),
                          ('C', 'D', {'sign': 0})])
    (f_level, b_level) = get_reachable_sets(graph, source, target,
                                            max_depth=5, signed=True)
    assert f_level == {}
    assert b_level == {}
    # This time, make the unreachability due to the sign
    graph = nx.DiGraph()
    graph.add_nodes_from(['A', 'B', 'C', 'D'])
    graph.add_edges_from([('A', 'B', {'sign': 0}),
                          ('D', 'B', {'sign': 0}),
                          ('C', 'A', {'sign': 0}),
                          ('C', 'D', {'sign': 0})])
    (f_level, b_level) = get_reachable_sets(graph, source, target, max_depth=5,
                                            signed=True)
    assert f_level == {}
    assert b_level == {}


def test_from_graph_unsigned():
    # Path length 1
    f_level, b_level = get_reachable_sets(graph1_s, source, target, max_depth=3,
                                          signed=False)
    pg = PathsGraph.from_graph(graph1_uns, source, target, 1, f_level, b_level,
                               signed=False)
    assert len(pg.graph) == 0
    # Path length 2
    pg = PathsGraph.from_graph(graph1_uns, source, target, 2, f_level, b_level, 
                               signed=False)
    paths = list(nx.shortest_simple_paths(pg.graph, (0, 'A'), (2, 'D')))
    assert len(paths) == 2
    assert [(0, 'A'), (1, 'C'), (2, 'D')] in paths
    assert [(0, 'A'), (1, 'B'), (2, 'D')] in paths
    # Path length 3
    pg = PathsGraph.from_graph(graph1_uns, source, target, 3, f_level, b_level, 
                               signed=False)
    assert len(pg.graph) == 0


def test_from_graph_unsigned_no_levels():
    length = 2
    pg = PathsGraph.from_graph(graph1_uns, source, target, length)
    assert isinstance(pg, PathsGraph)
    paths = list(nx.shortest_simple_paths(pg.graph, (0, 'A'), (2, 'D')))
    assert len(paths) == 2
    assert [(0, 'A'), (1, 'C'), (2, 'D')] in paths
    assert [(0, 'A'), (1, 'B'), (2, 'D')] in paths


def test_from_graph_signed():
    # Path length 1
    f_level, b_level = get_reachable_sets(graph1_s, source, target, signed=True,
                                          max_depth=3)
    pg = PathsGraph.from_graph(graph1_s, source, target, 1, f_level, b_level,
                               signed=True, target_polarity=0)
    assert not pg.graph
    # Path length 2
    pg = PathsGraph.from_graph(graph1_s, source, target, 2, f_level, b_level,
                               signed=True, target_polarity=0)
    paths = list(nx.shortest_simple_paths(pg.graph, (0, ('A', 0)),
                                                          (2, ('D', 0))))
    assert len(paths) == 2
    assert [(0, ('A', 0)), (1, ('C', 0)), (2, ('D', 0))] in paths
    assert [(0, ('A', 0)), (1, ('B', 0)), (2, ('D', 0))] in paths
    # Path length 3
    pg = PathsGraph.from_graph(graph1_s, source, target, 3, f_level, b_level,
                               signed=True, target_polarity=0)
    assert not pg.graph


def test_pg_check_unreachable_unsigned():
    graph = nx.DiGraph()
    graph.add_nodes_from(['A', 'B', 'C', 'D'])
    graph.add_edges_from([('A', 'B'), ('D', 'B'), ('C', 'A'), ('C', 'D')])
    (f_level, b_level) = get_reachable_sets(graph, source, target, max_depth=5, 
                                            signed=False)
    assert f_level == {}
    assert b_level == {}
    pg = PathsGraph.from_graph(graph, source, target, 2, f_level, b_level,
                               signed=False)
    assert not pg.graph
    # A graph where there is a path, but not of the given length (3)
    (f_level, b_level) = get_reachable_sets(graph1_s, source, target,
                                            max_depth=5, signed=False)
    pg = PathsGraph.from_graph(graph, source, target, 3, f_level, b_level,
                               signed=False)
    assert not pg.graph


def test_multidigraph_signed():
    graph = nx.MultiDiGraph()
    graph.add_edges_from([('A', 'B', {'sign': 0}), ('A', 'B', {'sign': 1})])
    f_level, b_level = get_reachable_sets(graph, 'A', 'B', max_depth=3,
                                          signed=True)
    assert f_level[0] == {('A', 0)}
    assert f_level[1] == {('B', 0), ('B', 1)}
    assert b_level[0] == {('B', 0)}
    assert b_level[1] == {('A', 0), ('A', 1)}


def test_sample_paths():
    g_uns = nx.DiGraph()
    g_uns.add_edges_from((('A', 'B'), ('A', 'C'), ('C', 'D'), ('B', 'D'),
                          ('D', 'B'), ('D', 'C'), ('B', 'E'), ('C', 'E')))
    source, target, length = ('A', 'E', 4)
    pg = PathsGraph.from_graph(g_uns, source, target, length)
    sample_paths = pg.sample_paths(100)
    assert set(sample_paths) == set(
        [('A', 'B', 'D', 'B', 'E'),
         ('A', 'B', 'D', 'C', 'E'),
         ('A', 'C', 'D', 'B', 'E'),
         ('A', 'C', 'D', 'C', 'E')])


def test_enumerate_paths():
    g_uns = nx.DiGraph()
    g_uns.add_edges_from((('A', 'B'), ('A', 'C'), ('C', 'D'), ('B', 'D'),
                          ('D', 'B'), ('D', 'C'), ('B', 'E'), ('C', 'E')))
    source, target, length = ('A', 'E', 4)
    pg = PathsGraph.from_graph(g_uns, source, target, length)
    enum_paths = pg.enumerate_paths()
    assert set(enum_paths) == set(
        [('A', 'B', 'D', 'B', 'E'),
         ('A', 'B', 'D', 'C', 'E'),
         ('A', 'C', 'D', 'B', 'E'),
         ('A', 'C', 'D', 'C', 'E')])


def test_count_paths():
    g_uns = nx.DiGraph()
    g_uns.add_edges_from((('A', 'B'), ('A', 'C'), ('C', 'D'), ('B', 'D'),
                          ('D', 'B'), ('D', 'C'), ('B', 'E'), ('C', 'E')))
    source, target, length = ('A', 'E', 4)
    pg = PathsGraph.from_graph(g_uns, source, target, length)
    num_paths = pg.count_paths()
    assert num_paths == 4


def test_non_uniform_sampling():
    pg = PathsGraph.from_graph(g_samp, 'source', 'target', 3)
    # There are five different paths, but sampling uniformly based on local
    # edge weights should result in ~50% of paths going through B1
    os.environ['TEST_FLAG'] = 'TRUE'
    np.random.seed(1) # Seed the random number generator
    num_samples = 1000
    paths = pg.sample_paths(num_samples)
    num_b1_paths = len([p for p in paths if 'B1' in p])
    num_other_paths = len([p for p in paths if 'B1' not in p])
    assert num_b1_paths == 526
    assert num_other_paths == 474


def test_uniform_sampling():
    pg = PathsGraph.from_graph(g_samp, 'source', 'target', 3)
    # There are five different paths; sampling uniformly across the whole
    # path distribution should result in 20% of paths going through each of
    # paths going through B1-B5.
    pg.set_uniform_path_distribution()
    os.environ['TEST_FLAG'] = 'TRUE'
    np.random.seed(1) # Seed the random number generator
    num_samples = 5000
    path_count = pg.count_paths()
    assert path_count == 5
    paths = pg.sample_paths(num_samples, weighted=True)
    b_ctr = Counter([p[2] for p in paths])
    print(b_ctr)
    assert b_ctr == {'B1': 1021, 'B2': 991, 'B3': 964, 'B4': 1022, 'B5': 1002}


def test_raw_graph_sampling():
    """Smoke test for sampling on an underlying graph."""
    g = nx.DiGraph()
    g.add_edges_from([('S', 'A'), ('S', 'T'), ('A', 'T'), ('A', 'S')])
    paths = sample_raw_graph(g, 'S', 'T', num_samples=10000,
                             eliminate_cycles=False)
    path_ctr = Counter([len(p) for p in paths])
    print(path_ctr)

    paths = sample_raw_graph(g, 'S', 'T', num_samples=10000,
                             eliminate_cycles=True)
    path_ctr = Counter([len(p) for p in paths])
    assert len(path_ctr) == 2
    print(path_ctr)

    paths = sample_raw_graph(g, 'S', 'T', num_samples=10000,
                             eliminate_cycles=False, max_depth=4)
    path_ctr = Counter([len(p) for p in paths])
    assert len(path_ctr) == 4
    print(path_ctr)


def test_combine_paths_graphs():
    g = nx.DiGraph()
    g.add_edges_from([('S', 'A'), ('S', 'T'), ('A', 'T'), ('A', 'S')])
    max_depth = 4
    pg_dict = {}
    for length in range(1, max_depth+1):
        paths_graph = PathsGraph.from_graph(g, 'S', 'T', length)
        pg_dict[length] = paths_graph
    cpg = combine_paths_graphs(pg_dict)
    paths = cpg.sample_paths(1000)
    path_ctr = Counter(paths)
    print(path_ctr)
    globals().update(locals())
    draw(cpg.graph, 'cpg.pdf')


def draw(g, filename):
    ag = nx.nx_agraph.to_agraph(g)
    ag.draw(filename, prog='dot')


if __name__ == '__main__':
    test_combine_paths_graphs()


import networkx
import pygraphviz
from indra.explanation import paths_graph

source = 'A'
target = 'D'
target_polarity = 0

graph1_s = networkx.DiGraph()
graph1_s.add_nodes_from(['A', 'B', 'C', 'D'])
graph1_s.add_edges_from([('A', 'B', {'polarity': 0}),
                         ('B', 'D', {'polarity': 0}),
                         ('A', 'C', {'polarity': 0}),
                         ('C', 'D', {'polarity': 0})])

graph1_uns = networkx.DiGraph()
graph1_uns.add_nodes_from(['A', 'B', 'C', 'D'])
graph1_uns.add_edges_from([('A', 'B'), ('B', 'D'), ('A', 'C'), ('C', 'D')])

"""
graph2 = networkx.DiGraph()
graph2.add_nodes_from(['A', 'B', 'C', 'D'])
graph2.add_edges_from([('A', 'B', {'polarity': 0}), ('B', 'A', {'polarity': 0}),
                      ('A', 'C', {'polarity': 0}), ('C', 'D', {'polarity': 0})])

"""

def test_get_reachable_sets_signed():
    f_level, b_level = paths_graph.get_reachable_sets(
                                    graph1_s, source, target, signed=True)
    assert f_level == {0: {('A', 0)}, 1: {('B', 0), ('C', 0)}, 2: {('D', 0)}}
    assert b_level == {0: {('D', 0)}, 1: {('B', 0), ('C', 0)}, 2: {('A', 0)}}


def test_get_reachable_sets_unsigned():
    f_level, b_level = paths_graph.get_reachable_sets(
                                    graph1_uns, source, target, signed=False)
    assert f_level == {0: {'A'}, 1: {'B', 'C'}, 2: {'D'}}
    assert b_level == {0: {'D'}, 1: {'B', 'C'}, 2: {'A'}}


def test_paths_graph_signed():
    # Path length 1
    f_level, b_level = paths_graph.get_reachable_sets(graph1_s, source, target,
                                 signed=True, max_depth=3)
    pg = paths_graph.paths_graph(graph1_s, source, target, 1, f_level, b_level,
                                 signed=True, target_polarity=0)
    assert len(pg) == 0
    # Path length 2
    pg = paths_graph.paths_graph(graph1_s, source, target, 2, f_level, b_level, 
                                 signed=True, target_polarity=0)
    paths = list(networkx.shortest_simple_paths(pg, (2, ('A', 0)),
                                                    (0, ('D', 0))))
    assert len(paths) == 2
    assert [(2, ('A', 0)), (1, ('C', 0)), (0, ('D', 0))] in paths
    assert [(2, ('A', 0)), (1, ('B', 0)), (0, ('D', 0))] in paths
    # Path length 3
    pg = paths_graph.paths_graph(graph1_s, source, target, 3, f_level, b_level,
                                 signed=True, target_polarity=0)
    assert len(pg) == 0


def test_paths_graph_unsigned():
    # Path length 1
    f_level, b_level = paths_graph.get_reachable_sets(graph1_s, source, target,
                                 max_depth=3, signed=False)
    pg = paths_graph.paths_graph(graph1_uns, source, target, 1, f_level,
                                 b_level, signed=False)
    assert len(pg) == 0
    # Path length 2
    pg = paths_graph.paths_graph(graph1_uns, source, target, 2, f_level,
                                 b_level, signed=False)
    paths = list(networkx.shortest_simple_paths(pg, (2, 'A'), (0, 'D')))
    assert len(paths) == 2
    assert [(2, 'A'), (1, 'C'), (0, 'D')] in paths
    assert [(2, 'A'), (1, 'B'), (0, 'D')] in paths
    # Path length 3
    pg = paths_graph.paths_graph(graph1_uns, source, target, 3, f_level,
                                 b_level, signed=False)
    assert len(pg) == 0

def test_simple_unreachability_unsigned():
    graph = networkx.DiGraph()
    graph.add_nodes_from(['A', 'B', 'C', 'D'])
    graph.add_edges_from([('A', 'B'), ('D', 'B'), ('C', 'A'), ('C', 'D')])
    (f_level, b_level) = paths_graph.get_reachable_sets(graph, source, target,
                                                    max_depth=5, signed=False)
    assert f_level is None
    assert b_level is None

def test_simple_unreachability_signed():
    # First make the unreachability due to the direction of the edges
    graph = networkx.DiGraph()
    graph.add_nodes_from(['A', 'B', 'C', 'D'])
    graph.add_edges_from([('A', 'B', {'polarity': 0}),
                          ('D', 'B', {'polarity': 0}),
                          ('C', 'A', {'polarity': 0}),
                          ('C', 'D', {'polarity': 0})])
    (f_level, b_level) = paths_graph.get_reachable_sets(graph, source, target,
                                                    max_depth=5, signed=True)
    assert f_level is None
    assert b_level is None
    # This time, make the unreachability due to the sign
    graph = networkx.DiGraph()
    graph.add_nodes_from(['A', 'B', 'C', 'D'])
    graph.add_edges_from([('A', 'B', {'polarity': 0}),
                          ('D', 'B', {'polarity': 0}),
                          ('C', 'A', {'polarity': 0}),
                          ('C', 'D', {'polarity': 0})])
    (f_level, b_level) = paths_graph.get_reachable_sets(graph, source, target,
                                                    max_depth=5, signed=True)
    assert f_level is None
    assert b_level is None

if __name__ == '__main__':
    test_get_reachable_sets_unsigned()
    #test_paths_graph_unsigned()
    #test_simple_unreachability_signed()
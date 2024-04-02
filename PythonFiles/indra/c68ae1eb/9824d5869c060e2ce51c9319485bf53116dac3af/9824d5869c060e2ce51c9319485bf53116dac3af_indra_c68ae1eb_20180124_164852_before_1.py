import logging
import itertools
import numpy as np
import networkx as nx
from .paths_graph import get_reachable_sets, PathsGraph
from .cfpg import CFPG

logger = logging.getLogger('paths_graph')


__all__ = ['load_signed_sif', 'sample_paths', 'enumerate_paths', 'count_paths',
           'sample_raw_graph']


def load_signed_sif(sif_file):
    """Load edges from a SIF file with lines of the form 'u polarity v'"""
    edges = []
    with open(sif_file, 'rt') as f:
        for line in f.readlines():
            u, polarity, v = line.strip().split(' ')
            # Eliminate self-loops
            if u == v:
                pass
            else:
                edges.append((u, v, {'sign': int(polarity)}))
    g = nx.DiGraph()
    g.add_edges_from(edges)
    return g


def sample_paths(g, source, target, max_depth=None, num_samples=1000,
                 cycle_free=True, signed=False, target_polarity=0):
    """Sample paths from a graph using PathsGraphs or CFPGs.

    This high-level function provides explicit access to path sampling
    without the user need to explicit create PathsGraphs or CFPGs for
    different path lengths.
    """
    return _run_by_depth('sample_paths', [num_samples], g, source, target,
                         max_depth, cycle_free, signed, target_polarity)


def enumerate_paths(g, source, target, max_depth=None,
                    cycle_free=True, signed=False, target_polarity=0):
    return _run_by_depth('enumerate_paths', [], g, source, target, max_depth,
                         cycle_free, signed, target_polarity)


def count_paths(g, source, target, max_depth=None,
                cycle_free=True, signed=False, target_polarity=0):
    return _run_by_depth('count_paths', [], g, source, target, max_depth,
                         cycle_free, signed, target_polarity)


def _run_by_depth(func_name, func_args, g, source, target, max_depth=None,
                  cycle_free=True, signed=False, target_polarity=0):
    if max_depth is None:
        max_depth = len(g)
    f_level, b_level = get_reachable_sets(g, source, target, max_depth,
                                          signed=signed)
    # Compute path graphs over a range of path lengths
    pg_by_length = {}
    if func_name == 'count_paths':
        results = 0
    else:
        results = []
    for path_length in range(1, max_depth+1):
        logger.info("Length %d: computing paths graph" % path_length)
        args = [g, source, target, path_length, f_level, b_level]
        kwargs = {'signed': signed, 'target_polarity': target_polarity}
        if cycle_free:
            pg = CFPG.from_graph(*args, **kwargs)
        else:
            pg = PathsGraph.from_graph(*args, **kwargs)
        pg_by_length[path_length] = pg
        # If we're sampling by depth, do sampling here
        if pg:
            #logger.info("Length %d: Sampling %d paths" %
            #            (path_length, num_samples))
            func = getattr(pg, func_name)
            results += func(*func_args)
    return results


def sample_raw_graph(g, source, target, max_depth=10, num_samples=1000,
                     eliminate_cycles=False):
    """Sample paths up to a given depth from an underlying graph.

    Useful for comparing the properties of sampling from paths graphs to
    sampling from the original graph.
    """
    paths = []
    if target not in g:
        raise ValueError("Target node %s not in graph" % target)
    # Check if any paths exist
    if not nx.has_path(g, source, target):
        return []
    while len(paths) < num_samples:
        node = source
        path = [source]
        while True:
            # If we haven't found the target within the specified depth,
            # terminate
            #if len(path) >= max_depth + 1:
            #    path = []
            #    break
            # Get a list of possible successor nodes
            if eliminate_cycles:
                successors = [e[1] for e in g.out_edges(node)
                                   if e[1] not in path]
            else:
                successors = [e[1] for e in g.out_edges(node)]
            # No non-cyclic successors; terminate
            if not successors:
                path = []
                break
            # Choose a successor node:
            # If we're one step before the maximum reachable depth,
            # always choose the target if it's available--this mimics
            # the behavior of the paths graph
            if len(path) == max_depth:
                if target in successors:
                    node = target
                else:
                    path = []
                    break
            else:
                succ_ix = np.random.choice(range(len(successors)))
                node = successors[succ_ix]
            # Add the current node to the path
            path.append(node)
            # Terminate if we reached the target
            if node == target:
                break
        # Only add the path if we successfully got one
        if path:
            paths.append(tuple(path))
    return paths


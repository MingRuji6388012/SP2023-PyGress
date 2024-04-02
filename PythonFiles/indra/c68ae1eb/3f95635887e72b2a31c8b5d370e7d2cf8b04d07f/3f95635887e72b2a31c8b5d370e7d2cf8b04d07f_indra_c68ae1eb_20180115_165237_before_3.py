import numpy as np
from copy import copy, deepcopy
import networkx as nx
from . import paths_graph
from .util import prune, check_reach_depth


def from_graph(g, source_name, target_name, path_length, fwd_reachset=None,
               back_reachset=None):
    """Compute a pre- cycle free paths graph.

    Starting from the "raw" (i.e., containing cycles) paths graph, and given a
    target path length n, the algorithm iterates over each "level" in the graph
    0 <= k <= n where level 0 consists only of the source node and level n
    consists only of the target.

    Each level k consists of a set of nodes, X; we examine each node x in X and
    identify the subset of nodes that are reachable in both the forward and
    backward directions from x. If any of the nodes in the forward reach
    subgraph contain x itself (but at a different depth), this represents a
    cyclic path back through x that is then pruned.

    Each node x therefore defines its own subgraph of cycle free paths, g_x.
    After iterating over all x in X, we combine these subgraphs into the
    (in-progress) cycle free paths graph H_k. H_k therefore consists of the
    superset of nodes of all the subgraphs g_x for level k. When merging these
    subgraphs we prevent the re-introduction of cyclic paths by annotating each
    node in the graph with a list of "tags". The tags for any given node
    consist of a list of nodes lying at prior (upstream) levels. Therefore
    during sampling, transitions from an upstream node to a downstream node are
    only permissible if all nodes in the path up to a certain level are
    contained in the tag set of the downstream node.

    Parameters
    ----------
    g : networkx.DiGraph()
        Original graph used to compute the pre-CFPG.
    source_name : str
        Name of the source node.
    target_name : str
        Name of the target node.
    path_length : int
        Desired path length.
    fwd_reachset : Optional[dict]
        Dictionary representing the forward reachset computed over the original
        graph g up to a maximum depth greater than the requested path length.
        If not provided, the forward reach set is calculated up to the
        requested path length up to the requested path length by calling
        paths_graph.get_reachable_sets.
    back_reachset : Optional[dict]
        Dictionary representing the backward reachset computed over the
        original graph g up to a maximum depth greater than the requested path
        length.  If not provided, the backward reach set is calculated up to
        the requested path length up to the requested path length by calling
        paths_graph.get_reachable_sets.

    Returns
    -------
    PreCFPG
        A instance of the PreCFPG the containing the pre- cycle free paths
        graph.
    """
    # If the reachable sets aren't provided by the user, compute them here
    # with a maximum depth given by the target path length.
    if fwd_reachset is None or back_reachset is None:
        (fwd_reachset, back_reachset) = paths_graph.get_reachable_sets(
                        g, source_name, target_name, max_depth=path_length)
    # Otherwise, if the reachable sets are provided, use them after checking
    # if they have a depth at least equal to the given path length
    check_reach_depth('forward', fwd_reachset, path_length)
    check_reach_depth('backward', back_reachset, path_length)
    pg = paths_graph.from_graph(g, source_name, target_name, path_length,
                                fwd_reachset, back_reachset)
    return from_pg(pg)


def from_pg(pg):
    """Compute a pre- cycle free paths graph.

    Starting from the "raw" (i.e., containing cycles) paths graph, and given a
    target path length n, the algorithm iterates over each "level" in the graph
    0 <= k <= n where level 0 consists only of the source node and level n
    consists only of the target.

    Each level k consists of a set of nodes, X; we examine each node x in X and
    identify the subset of nodes that are reachable in both the forward and
    backward directions from x. If any of the nodes in the forward reach
    subgraph contain x itself (but at a different depth), this represents a
    cyclic path back through x that is then pruned.

    Each node x therefore defines its own subgraph of cycle free paths, g_x.
    After iterating over all x in X, we combine these subgraphs into the
    (in-progress) cycle free paths graph H_k. H_k therefore consists of the
    superset of nodes of all the subgraphs g_x for level k. When merging these
    subgraphs we prevent the re-introduction of cyclic paths by annotating each
    node in the graph with a list of "tags". The tags for any given node
    consist of a list of nodes lying at prior (upstream) levels. Therefore
    during sampling, transitions from an upstream node to a downstream node are
    only permissible if all nodes in the path up to a certain level are
    contained in the tag set of the downstream node.

    Parameters
    ----------
    pg : networkx.DiGraph()
        "Raw" (contains cycles) paths graph as created by
        :py:func:`indra.explanation.paths_graph.from_graph`.

    Returns
    -------
    PreCFPG
        A instance of the PreCFPG the containing the pre- cycle free paths
        graph.
    """
    # Initialize the cycle-free paths graph and the tag dictionary
    source_node = pg.source_node
    target_node = pg.target_node
    dic_PG = {0: _initialize_pre_cfpg(pg)}
    round_counter = 1
    # Perform CFPG generation in successive rounds to ensure convergence
    while True:
        #print("Starting round %d" % round_counter)
        #print("Level 0: %d nodes, %d edges" % (len(dic_PG[0][0]),
                                               #len(dic_PG[0][0].edges())))
        for k in range(1, pg.path_length+1):
            # Start by copying the information from the previous level
            H = dic_PG[k-1][0].copy()
            tags = deepcopy(dic_PG[k-1][1])
            # Check if we have already detected there are no cycle free paths,
            # which would be indicated by an empty graph at the previous level.
            # If so just propagate this information.
            if not H:
                dic_PG[k] = dic_PG[k-1]
            else:
                # Identify the nodes at level k in G_(k-1)
                X = [v for v in H.nodes_iter() if v[0] == k]
                # We will track the (g_x, tags_x) pairs contributed by each x
                # through dic_X
                dic_X = {}
                for x in X:
                    tags_x = {}
                    g_x_f = _forward(x, H, pg.path_length)
                    g_x_b = _backward(x, H)
                    g_x = nx.DiGraph()
                    g_x.add_edges_from(g_x_b.edges())
                    g_x.add_edges_from(g_x_f.edges())
                    # Get the nodes in the forward reach set representing cycles
                    # back through node x, (excluding x at level k)
                    nodes_to_prune = [v for v in g_x_f
                                      if v[1] == x[1] and v[0] != k]
                    # If there are no nodes to prune then just add the tag 'x'
                    # to all the nodes in g_x_f but not to x
                    g_x_prune = prune(g_x, nodes_to_prune, source_node,
                                      target_node)
                    # If target or x gets pruned then x will contribute
                    # nothing to G_k
                    if (target_node not in g_x_prune) or (x not in g_x_prune):
                        pass
                    nodes_to_tag = [v for v in g_x_prune.nodes()
                                    if v[0] >= k]
                    # Otherwise add the tag x to the nodes in the strict
                    # future of x and update dic_X
                    for v in g_x_prune.nodes_iter():
                        if v[0] >= k:
                            D = tags[v]
                            D.append(x)
                            tags_x[v] = D
                        else:
                            tags_x[v] = tags[v]
                    dic_X[x] = (g_x_prune, tags_x)
                # We can now piece together the pairs in dic_X to obtain (G_k,
                # tags_k)
                H_k = nx.DiGraph()
                tags_k = {}
                for x in X:
                    h_x = dic_X[x][0]
                    H_k.add_edges_from(h_x.edges())
                for v in H_k.nodes_iter():
                    t = []
                    for x in X:
                        if v in dic_X[x][0]:
                            tags_x = dic_X[x][1]
                            t.extend(tags_x[v])
                    t = list(set(t))
                    tags_k[v] = t
                dic_PG[k] = (H_k, tags_k)
            #print("Level %d: %d nodes, %d edges" % (k, len(dic_PG[k][0]),
                                                    #len(dic_PG[k][0].edges())))
        if not dic_PG[len(dic_PG)-1][0] or \
           set(dic_PG[0][0].edges()) == set(dic_PG[len(dic_PG)-1][0].edges()):
            break
        else:
            dic_PG = {0: dic_PG[k]}
        round_counter += 1
    pre_cfpg, tags = dic_PG[pg.path_length]
    # Return only the fully processed cfpg as an instance of the PreCFPG class
    return PreCFPG(pg, pre_cfpg, tags)


class PreCFPG(object):
    """Representation of a pre- cycle free paths graph with associated methods.

    The pre- cycle free paths graph consists of the paths graph remaining after
    cycles through the source or target nodes are removed. However, paths
    through the pre-CFPG node structure itself are not guaranteed to be cycle
    free; instead, cycle-free paths can be sampled by taking into account
    the tags associated with each node, representing the possible cycle-free
    histories of the node in terms of other upstream nodes.

    As with the "raw" paths graph (containing cycles), nodes in the pre-CFPG
    consist of tuples with two elements: (depth, name).

    Parameters
    ----------
    pg : networkx.DiGraph()
        "Raw" (contains cycles) paths graph as created by
        :py:func:`indra.explanation.paths_graph.from_graph`.
    graph : networkx.DiGraph
        The graph structure of the pre-CFPG.
    tags : dict
        A dictionary, keyed by node, with lists of other nodes representing
        the nodes lying upstream on cycle free paths. Node that each node
        also has itself as a tag.

    Attributes
    ----------
    source_node : tuple
        Node in the pre-CFPG graph representing the source: (0, source_name)
    target_node: tuple
        Node in the pre-CFPG graph representing the target:
        (path_length, target_name)
    """
    def __init__(self, pg, graph, tags):
        self.source_name = pg.source_name
        self.source_node = pg.source_node
        self.target_name = pg.target_name
        self.target_node = pg.target_node
        self.path_length = pg.path_length
        self.graph = graph
        self.tags = tags

    def sample_paths(self, num_paths):
        """Sample cycle-free paths from the pre-CFPG.

        Parameters
        ----------
        num_paths : int
            The number of paths to sample.

        Returns
        -------
        list of tuples
            Each item in the list is a tuple of strings representing a path.
            Note that the paths may not be unique.
        """
        # If the graph is empty, then there are no paths
        if not self.graph:
            return []
        P = []
        for i in range(0, num_paths):
            p = self.sample_single_path()
            P.append(p)
        return P

    def sample_single_path(self):
        """Sample a single cycle-free path using the pre-CFPG.

        The sampling procedure uses the tag sets to trace out cycle-free paths.
        If we have reached a node *v* via the path *p* then we can choose the
        successor *u* of *v* as the next node only if *p* appears in the tag
        set of u.

        Returns
        -------
        tuple of strings
            A randomly sampled, non-cyclic path. Nodes are represented as node
            names only, i.e., the depth prefixes are removed.
        """
        path = [self.source_node]
        current = self.source_node
        while current != self.target_node:
            next = self._successor(path, current)
            path.append(next)
            current = next
        return tuple(path)

    def _successor(self, path, v):
        """Randomly choose a successor node of v given the current path.

        Parameters
        ----------
        path : list
            The path so far (list of nodes).
        v : tuple
            The current node.

        Returns
        -------
        tuple
            Randomly chosen successor node on a non-cyclic path.
        """
        succ = []
        for u in self.graph.successors(v):
            if set(path) <= set(self.tags[u]):
                succ.append(u)
        # Note that the circuitous way of choosing from this list is the
        # result of the odd way numpy.random handles lists of lists (it
        # excepts).
        idx_list = list(range(len(succ)))
        w_idx = np.random.choice(idx_list)
        w = succ[w_idx]
        return w

    @staticmethod
    def name_paths(paths):
        pass


def _initialize_pre_cfpg(pg):
    """Initialize pre- cycle free paths graph data structures.

    Parameters
    ----------
    pg : PathsGraph
        "Raw" (contains cycles) paths graph as created by
        :py:func:`indra.explanation.paths_graph.paths_graph`.
    source_node : tuple
        Source node, of the form (0, source_name).
    target_node : tuple
        Target node, of the form (target_depth, source_name).

    Returns
    -------
    tuple : (networkx.DiGraph(), dict)
    """
    # Identify the initial set of nodes to be pruned. In this initial phase,
    # they are simply nodes whose names match the source or target.
    nodes_to_prune = set([v for v in pg.graph.nodes_iter()
                        if (v != pg.source_node) and (v != pg.target_node) and \
                             ((v[1] == pg.source_node[1]) or \
                              (v[1] == pg.target_node[1]))])
    # Get the paths graph after initial source_node/target_node cycle pruning
    pre_cfpg_0 = prune(pg.graph, nodes_to_prune, pg.source_node, pg.target_node)
    # Initialize an empty list of tags for each node
    tags = dict([(node, []) for node in pre_cfpg_0.nodes_iter()])
    # Add source_node tag to all nodes
    _add_tag(tags, pg.source_node, [v for v in pre_cfpg_0.nodes()])
    return (pre_cfpg_0, tags)


def _add_tag(tag_dict, tag_node, nodes_to_tag):
    for v in nodes_to_tag:
        tag_dict[v].append(tag_node)


def _forward(v, H, length):
    """Compute the subgraph of H defined by the paths forward from node v.

    Parameters
    ----------
    v : tuple(int, str)
        The node to get the _forward subgraph for.
    H : networkx.DiGraph()
        For a given path length n, H defines the graph G_i at the i-th stage
        for 1 <= i <= n.
    Returns
    -------
    networkx.DiGraph()
        Subgraph reachable by forward paths from v in H.
    """
    j = v[0]
    L = {}
    L[j] = [v]
    h = nx.DiGraph()
    for k in range(j+1, length+1):
        for v in L[k - 1]:
            h.add_edges_from(H.out_edges(v))
        L[k] = [w for w in h if w[0] == k]
    return h


def _backward(v, H):
    """Compute the subgraph of H defined by the paths backward from node v.

    Parameters
    ----------
    v : tuple(int, str)
        The node to get the _backward subgraph for.
    H : networkx.DiGraph()
        For a given path length n, H defines the graph G_i at the i-th stage
        for 1 <= i <= n.

    Returns
    -------
    networkx.DiGraph()
        Subgraph reachable by backward paths from v in H.
    """
    j = v[0]
    L = {}
    L[j] = [v]
    J =  list(reversed(range(0, j)))
    h = nx.DiGraph()
    for k in J:
        for v in L[k+1]:
            h.add_edges_from(H.in_edges(v))
        L[k] = [w for w in h if w[0] == k]
    return h


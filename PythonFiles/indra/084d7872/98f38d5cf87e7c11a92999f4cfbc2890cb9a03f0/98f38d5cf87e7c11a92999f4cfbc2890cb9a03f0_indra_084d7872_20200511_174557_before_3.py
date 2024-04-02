"""This script loads the ontologies for Eidos and Hume and generates RDFs.

The script can handle any ontology which uses the same format (yaml ontology
following the namespace defined at `eidos_ns`).
"""
import yaml
import requests
from collections import defaultdict
from ..ontology_graph import IndraOntology, label


wm_ont_url = ('https://raw.githubusercontent.com/WorldModelers/'
              'Ontologies/master/wm_metadata.yml')


def get_term(node, prefix):
    node = node.replace(' ', '_')
    path = prefix + '/' + node if prefix else node
    return label('WM', path)


def load_yaml_from_url(ont_url):
    """Return a YAML object loaded from a YAML file URL."""
    res = requests.get(ont_url)
    res.raise_for_status()
    root = yaml.load(res.content, Loader=yaml.FullLoader)
    return root


class WorldOntology(IndraOntology):
    def __init__(self, url):
        super().__init__()
        self.add_wm_ontology(url)

    def add_wm_ontology(self, url):
        yml = load_yaml_from_url(url)
        for top_entry in yml:
            node = list(top_entry.keys())[0]
            self.build_relations(node, top_entry[node], None)

    def build_relations(self, node, tree, prefix):
        nodes = defaultdict(dict)
        edges = []
        this_term = get_term(node, prefix)
        node = node.replace(' ', '_')
        if prefix is not None:
            prefix = prefix.replace(' ', '_')
        this_prefix = prefix + '/' + node if prefix else node
        for entry in tree:
            if isinstance(entry, str):
                continue
            elif isinstance(entry, dict):
                if 'OntologyNode' not in entry.keys():
                    for child in entry.keys():
                        if child[0] != '_' and child != 'examples' \
                                and isinstance(entry[child], (list, dict)):
                            self.build_relations(child, entry[child],
                                                 this_prefix)
                else:
                    child = entry['name']

            if child[0] != '_' and child != 'examples':
                child_term = get_term(child, this_prefix)
                edges.append((child_term, this_term, {'rel': 'isa'}))
                opp = entry.get('opposite')
                if opp:
                    parts = opp.split('/')
                    opp_term = get_term(parts[-1], '/'.join(parts[:-1]))
                    edges.append((opp_term, child_term, {'rel': 'is_opposite'}))
                    edges.append((child_term, opp_term, {'rel': 'is_opposite'}))
                pol = entry.get('polarity')
                if pol is not None:
                    nodes[child_term]['polarity'] = pol
        self.add_nodes_from([(k, v) for k, v in dict(nodes).items()])
        self.add_edges_from(edges)


world_ontology = WorldOntology(wm_ont_url)

"""This file contains the methods needed to load the ontologies for Eidos.

It also loads BBN and can easly handle any other ontology which uses the same
format (yaml ontology following the namespace defined at `eidos_ns`).
"""

import yaml
import requests
from os.path import join, dirname, abspath
from rdflib import Graph, Namespace, Literal


eidos_ns = Namespace('https://github.com/clulab/eidos/wiki/JSON-LD/Grounding#')
indra_ns = 'http://sorger.med.harvard.edu/indra/'
indra_rel_ns = Namespace(indra_ns + 'relations/')
isa = indra_rel_ns.term('isa')


def save_hierarchy(g, path):
    with open(path, 'wb') as out_file:
        g_bytes = g.serialize(format='nt')
        # Replace extra new lines in string and get rid of empty line at end
        g_bytes = g_bytes.replace(b'\n\n', b'\n').strip()
        # Split into rows and sort
        rows = g_bytes.split(b'\n')
        rows.sort()
        g_bytes = b'\n'.join(rows)
        out_file.write(g_bytes)


def get_term(node, prefix):
    node = node.replace(' ', '_')
    path = prefix + '/' + node if prefix else node
    return eidos_ns.term(path)


def build_relations(G, node, tree, prefix):
    this_term = get_term(node, prefix)
    node = node.replace(' ', '_')
    if prefix is not None:
        prefix = prefix.replace(' ', '_')
    this_prefix = prefix + '/' + node if prefix else node
    for entry in tree:
        if isinstance(entry, str) and entry[0] != '_':
            child = entry
        elif isinstance(entry, dict):
            for child in entry.keys():
                if child[0] != '_' and child != 'examples' \
                   and any(isinstance(entry[child], t) for t in [list, dict]):
                    build_relations(G, child, entry[child], this_prefix)

        if child[0] != '_' and child != 'examples':
            child_term = get_term(child, this_prefix)
            rel = (child_term, isa, this_term)
            G.add(rel)


def load_ontology(ont_url, rdf_path):
    """Load an ontology formatted like Eidos' from github."""
    yml = requests.get(ont_url).content
    root = yaml.load(yml)
    G = Graph()
    for top_entry in root:
        assert len(top_entry) == 1
        node = list(top_entry.keys())[0]
        build_relations(G, node, top_entry[node], None)
    save_hierarchy(G, rdf_path)


if __name__ == '__main__':
    # Eidos
    from indra.sources import eidos
    eidos_ont_url = ('https://raw.githubusercontent.com/clulab/eidos/master/'
                     'src/main/resources/org/clulab/wm/eidos/ontologies/'
                     'un_ontology.yml')
    eidos_rdf_path = join(dirname(abspath(eidos.__file__)),
                          'eidos_ontology.rdf')
    load_ontology(eidos_ont_url, eidos_rdf_path)

    # BBN
    from indra.sources import bbn
    bbn_ont_url = ('https://raw.githubusercontent.com/BBN-E/Hume/master/'
                   'resource/ontologies/hume_ontology.yaml')
    bbn_rdf_path = join(dirname(abspath(bbn.__file__)), 'bbn_ontology.rdf')
    load_ontology(bbn_ont_url, bbn_rdf_path)
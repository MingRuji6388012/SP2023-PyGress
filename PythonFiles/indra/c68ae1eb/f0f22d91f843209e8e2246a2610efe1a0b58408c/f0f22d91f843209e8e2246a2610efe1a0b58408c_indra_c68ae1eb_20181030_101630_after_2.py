from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str
from os.path import abspath, dirname, join, exists
import pickle
import rdflib
from rdflib import Namespace, Literal
from indra.databases import go_client

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


def make_component_hierarchy(component_map, component_part_map):
    g = rdflib.Graph()
    indra_ns = 'http://sorger.med.harvard.edu/indra/'
    ln = Namespace(indra_ns + 'locations/')
    rn = Namespace(indra_ns + 'relations/')
    part_of = rn.term('partof')
    has_name = rn.term('hasName')
    for comp_id, comp_name in component_map.items():
        g.add((ln.term(comp_id), has_name, Literal(comp_name)))
        sups = component_part_map.get(comp_id)
        if sups is not None:
            for sup_id in sups:
                g.add((ln.term(comp_id), part_of, ln.term(sup_id)))
    return g


def main():
    # This file can be donwloaded from:
    # http://geneontology.org/ontology/go.owl
    pkl_file = join(dirname(abspath(__file__)), '../../data/go.pkl')
    rdf_file = join(dirname(abspath(__file__)),
                    '../resources/cellular_component_hierarchy.rdf')
    if not exists(pkl_file):
        g = go_client.load_go_graph()
        print("Pickling GO graph in %s" % pkl_file)
        with open(pkl_file, 'wb') as fh:
            pickle.dump(g, fh, protocol=2)
    else:
        print('Loading cached RDF graph from %s' % pkl_file)
        with open(pkl_file, 'rb') as fh:
            g = pickle.load(fh)
    print('Getting cellular components')
    component_map, component_part_map = go_client.get_cellular_components(g)
    gg = make_component_hierarchy(component_map, component_part_map)
    save_hierarchy(gg, rdf_file)

if __name__ == '__main__':
    main()
